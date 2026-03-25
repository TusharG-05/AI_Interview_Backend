import os
import json
import httpx
import re
import asyncio
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from ..core.database import get_db as get_session
from ..auth.dependencies import get_current_user, get_admin_user
from ..models.db_models import User
from ..core.logger import get_logger
from groq import AsyncGroq

load_dotenv()
logger = get_logger(__name__)
router = APIRouter(prefix="/agent", tags=["AI Agent"])

# --- Models ---

class AgentTaskRequest(BaseModel):
    task_description: str

class CandidateAnalysisRequest(BaseModel):
    candidate_name: str
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    email: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "admin_chat_001"

# --- Production Tool Registry (Strict Schema Enforcement) ---

TOOL_REGISTRY = {
    "list_candidates": {
        "description": "List candidates with search and pagination. Use this to find a candidate's numeric integer ID.",
        "method": "GET",
        "endpoint": "/api/admin/candidates",
        "query_params": {
            "search": {"type": "string", "description": "Keyword to search in full_name or email"},
            "skip": {"type": "integer", "description": "Number of records to skip", "default": 0},
            "limit": {"type": "integer", "description": "Number of records to return", "default": 20}
        }
    },
    "get_user_details": {
        "description": "Fetch full details of a specific user. REQUIRES numeric integer ID.",
        "method": "GET",
        "endpoint": "/api/admin/users/{id}",
        "path_params": {
            "id": {"type": "integer", "description": "Mandatory numeric ID (must be an integer)"}
        }
    },
    "list_papers": {
        "description": "List all available MCQ/Standard interview papers. Use this to find a paper_id.",
        "method": "GET",
        "endpoint": "/api/admin/papers"
    },
    "list_coding_papers": {
        "description": "List all available coding interview papers. Use this to find a coding_paper_id.",
        "method": "GET",
        "endpoint": "/api/admin/coding-papers"
    },
    "schedule_interview": {
        "description": "Schedule an interview. Requires numeric candidate_id and optional paper_ids.",
        "method": "POST",
        "endpoint": "/api/admin/interviews/schedule",
        "body_params": {
            "candidate_id": {"type": "integer", "description": "Numeric ID of the candidate"},
            "paper_id": {"type": "integer", "description": "Optional numeric ID of the MCQ paper"},
            "coding_paper_id": {"type": "integer", "description": "Optional numeric ID of the coding paper"},
            "schedule_time": {"type": "string", "description": "ISO 8601 datetime string (YYYY-MM-DDTHH:MM:SSZ)"},
            "interview_round": {"type": "string", "description": "Round name (e.g. 'Standard', 'Technical')"},
            "duration_minutes": {"type": "integer", "description": "Duration in minutes", "default": 1440},
            "max_questions": {"type": "integer", "description": "Max questions allowed", "default": 0}
        }
    },
    "list_results": {
        "description": "Fetch all candidate interview results and audit logs.",
        "method": "GET",
        "endpoint": "/api/admin/users/results"
    }
}

# --- Core Components ---

class SchemaValidator:
    @staticmethod
    def validate(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        tool = TOOL_REGISTRY.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found in registry.")

        validated_args = {}
        errors = []

        # Helper to validate params
        def validate_params(params_cfg, source_args, target_dict):
            for p_name, p_cfg in params_cfg.items():
                val = source_args.get(p_name)
                if val is None:
                    if "default" in p_cfg:
                        target_dict[p_name] = p_cfg["default"]
                    else:
                        errors.append(f"Missing mandatory parameter: {p_name}")
                    continue

                expected_type = p_cfg.get("type")
                if expected_type == "integer":
                    try:
                        target_dict[p_name] = int(str(val))
                    except (ValueError, TypeError):
                        errors.append(f"Parameter '{p_name}' must be an integer. Got: {val}")
                elif expected_type == "string":
                    target_dict[p_name] = str(val)
                else:
                    target_dict[p_name] = val

        if "path_params" in tool:
            validate_params(tool["path_params"], args, validated_args)
        if "query_params" in tool:
            validate_params(tool["query_params"], args, validated_args)
        if "body_params" in tool:
            validate_params(tool["body_params"], args, validated_args)

        if errors:
            raise ValueError(" ; ".join(errors))
        
        return validated_args

class ProductionAgent:
    def __init__(self, groq_key: str, fastapi_app: Any, auth_token: str):
        self.client = AsyncGroq(api_key=groq_key)
        self.fastapi_app = fastapi_app
        self.auth_token = auth_token
        self.max_steps = 10
        self.max_retries = 2
        self.context_history = []

    async def _call_llm(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        try:
            completion = await self.client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                temperature=0.0,
                top_p=1,
                response_format={"type": "json_object"} if json_mode else None
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API Error: {e}")
            return f"SYSTEM ERROR: {str(e)}"

    async def _generate_plan(self, user_query: str) -> List[str]:
        prompt = (
            "You are a strategic planner for an AI Agent. Given a user query and a list of tools, "
            "generate a step-by-step execution plan.\n\n"
            f"TOOLS:\n{json.dumps(TOOL_REGISTRY, indent=2)}\n\n"
            "Respond ONLY with a JSON object: {\"plan\": [\"step 1\", \"step 2\", ...]}"
        )
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Query: {user_query}"}
        ]
        resp = await self._call_llm(messages, json_mode=True)
        try:
            return json.loads(resp).get("plan", [])
        except:
            return ["Attempting to fulfill request directly."]

    async def _execute_api(self, tool_name: str, args: Dict[str, Any]) -> str:
        tool = TOOL_REGISTRY.get(tool_name)
        if not tool:
            return f"Error: Tool '{tool_name}' not found."

        try:
            validated_args = SchemaValidator.validate(tool_name, args)
        except ValueError as e:
            return f"VALIDATION ERROR: {str(e)}"

        method = tool["method"]
        endpoint = tool["endpoint"]
        
        # Resolve Path Params
        if "path_params" in tool:
            for p_name in tool["path_params"]:
                endpoint = endpoint.replace(f"{{{p_name}}}", str(validated_args[p_name]))
        
        # Prepare Body and Query
        body = {k: validated_args[k] for k in tool.get("body_params", {}) if k in validated_args}
        query = {k: validated_args[k] for k in tool.get("query_params", {}) if k in validated_args}

        try:
            base_url = "http://internal.api"
            transport = httpx.ASGITransport(app=self.fastapi_app)
            async with httpx.AsyncClient(transport=transport, base_url=base_url) as http_client:
                logger.info(f"Agent executing {tool_name}: {method} {endpoint} (Validated Args: {validated_args})")
                resp = await http_client.request(
                    method=method,
                    url=f"{base_url}{endpoint}",
                    json=body if body else None,
                    params=query if query else None,
                    headers={"Authorization": self.auth_token},
                    timeout=30.0,
                    follow_redirects=True
                )
                return f"HTTP {resp.status_code}: {resp.text}"
        except Exception as e:
            return f"NETWORK ERROR: {str(e)}"

    async def run(self, user_query: str) -> Dict[str, Any]:
        plan = await self._generate_plan(user_query)
        logger.info(f"Agent Plan: {plan}")

        system_instructions = (
            "You are a Production AI Agent for the Interview Platform.\n"
            f"STRATEGIC PLAN: {json.dumps(plan)}\n\n"
            "AVAILABLE TOOLS:\n" + json.dumps(TOOL_REGISTRY, indent=2) + "\n\n"
            "STRICT RULES:\n"
            "1. You MUST generate a 'Thought' and then an 'Action' or 'Final Answer'.\n"
            "2. 'Action' must be a single JSON block: {\"tool\": \"name\", \"args\": {}}\n"
            "3. If an API returns 'HTTP 422', ANALYZE the error and FIX your arguments in the next step.\n"
            "4. NEVER hallucinate IDs. Use 'list_candidates' to find them.\n"
            "5. Once finished, respond with 'Final Answer: <clean summary>'.\n"
        )

        messages = [{"role": "system", "content": system_instructions}]
        messages.append({"role": "user", "content": user_query})
        
        api_summary = []
        
        for step in range(self.max_steps):
            response = await self._call_llm(messages)
            messages.append({"role": "assistant", "content": response})
            
            if "Final Answer:" in response:
                return {
                    "reply": response.split("Final Answer:")[-1].strip(),
                    "api_calls": api_summary,
                    "status": "success",
                    "plan": plan
                }
            
            action_match = re.search(r'Action:\s*(\{.*\})', response, re.DOTALL)
            if not action_match:
                action_match = re.search(r'(\{.*\})', response, re.DOTALL)

            if action_match:
                try:
                    action_json = json.loads(action_match.group(1))
                    tool_name = action_json.get("tool")
                    args = action_json.get("args", {})
                    
                    api_summary.append(tool_name)
                    observation = await self._execute_api(tool_name, args)
                    
                    # Self-Healing Logic for 422
                    if "HTTP 422" in observation:
                        logger.warning(f"Detection of 422 error. Prompting agent to self-heal. Observation: {observation}")
                        messages.append({"role": "user", "content": f"Observation: {observation}\nSYSTEM NOTE: This is a validation error. Please check the parameter types and registry schema, then try again with CORRECTED values."})
                    else:
                        messages.append({"role": "user", "content": f"Observation: {observation}"})
                except Exception as e:
                    messages.append({"role": "user", "content": f"Observation: Error parsing your action JSON: {str(e)}"})
            else:
                messages.append({"role": "user", "content": "Observation: No valid Action JSON found. Use Thought/Action/Observation loop."})

        return {
            "reply": "Execution limit reached.",
            "api_calls": api_summary,
            "status": "partial",
            "plan": plan
        }

@router.post("/chat", response_model=Dict[str, Any])
async def chat_with_admin(
    chat_request: ChatRequest,
    fastapi_request: Request,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_session)
):
    groq_key = os.getenv("GROQ_API_KEY")
    agent = ProductionAgent(
        groq_key=groq_key, 
        fastapi_app=fastapi_request.app, 
        auth_token=fastapi_request.headers.get("Authorization")
    )
    return await agent.run(chat_request.message)

@router.post("/analyze-candidate", response_model=Dict[str, Any])
async def analyze_candidate_agent(
    request: CandidateAnalysisRequest,
    fastapi_request: Request,
    current_user: User = Depends(get_current_user)
):
    groq_key = os.getenv("GROQ_API_KEY")
    agent = ProductionAgent(
        groq_key=groq_key, 
        fastapi_app=fastapi_request.app, 
        auth_token=fastapi_request.headers.get("Authorization")
    )
    query = f"Provide a technical profile analysis for candidate: {request.candidate_name}. "
    if request.github_url: query += f"GitHub: {request.github_url} "
    if request.linkedin_url: query += f"LinkedIn: {request.linkedin_url} "
    
    result = await agent.run(query)
    return {
        "candidate_name": request.candidate_name,
        "analysis": result["reply"],
        "api_debug": result["api_calls"]
    }
