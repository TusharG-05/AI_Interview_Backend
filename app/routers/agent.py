import os
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any

from ..core.logger import get_logger
from ..core.database import get_db as get_session
from ..models.db_models import User, QuestionPaper, InterviewSession, InterviewStatus, CandidateStatus
from sqlmodel import Session, select
from .auth import get_current_user
from ..auth.dependencies import get_admin_user
from openclaw import AsyncOpenClaw
from datetime import datetime
import json
import httpx
import re

logger = get_logger(__name__)
router = APIRouter(prefix="/agent", tags=["OpenClaw Agent"])

class AgentTaskRequest(BaseModel):
    task_description: str
    workspace_name: Optional[str] = "interview_workspace"

class CandidateAnalysisRequest(BaseModel):
    candidate_name: str
    email: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    workspace_name: Optional[str] = "candidate_research"

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "admin_chat_001"
    
@router.post("/run-task", response_model=Dict[str, Any])
async def run_agent_task(
    request: AgentTaskRequest, 
    current_user: User = Depends(get_current_user)
):
    """
    Triggers an OpenClaw agent to perform an autonomous task.
    Requires OPENCLAW_API_KEY environment variable.
    """
    api_key = os.getenv("OPENCLAW_API_KEY", "dummy_key_for_testing")
    
    try:
        # Initialize async OpenClaw client (wraps CMDOP)
        # Using a dummy key for dry-run/testing if an actual key isn't provided,
        # but in production OPENCLAW_API_KEY must be set to a valid CMDOP API Key.
        async with AsyncOpenClaw.remote(api_key=api_key) as client:
            logger.info(f"Triggering OpenClaw task: {request.task_description}")
            
            # The exact API call depends on openclaw SDK specifics.
            # Using the documented cmdop style access for agent:
            if hasattr(client, 'agent'):
                # Assuming client.agent.run is the primary entry point
                result = await client.agent.run(request.task_description)
                
                return {
                    "status": "success",
                    "message": "Task completed by OpenClaw agent",
                    "result": str(result)
                }
            else:
                logger.warning("OpenClaw client missing 'agent' attribute. Simulating successful connection.")
                return {
                    "status": "pending",
                    "message": "OpenClaw agent connection simulated. Method execution requires full SDK implementation.",
                    "result": f"Simulated execution of: {request.task_description}"
                }
                
    except Exception as e:
        logger.error(f"Failed to execute OpenClaw task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-candidate", response_model=Dict[str, Any])
async def analyze_candidate_profile(
    request: CandidateAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Directs the OpenClaw agent to research a candidate's profiles using their 
    name, email, or direct URLs, and summarize their technical seniority and skills.
    """
    if not request.github_url and not request.linkedin_url and not request.email:
        raise HTTPException(status_code=400, detail="At least one identifier (email, github, or linkedin) must be provided.")
        
    api_key = os.getenv("OPENCLAW_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENCLAW_API_KEY environment variable is not configured.")
        
    # Construct the instruction prompt for the autonomous agent
    instruction = (
        f"You are a Senior Technical AI Recruiter. Your task is to analyze the candidate: '{request.candidate_name}'.\n"
    )
    
    if request.email and not (request.github_url and request.linkedin_url):
        instruction += f"1. Use your web search capabilities to find the GitHub and LinkedIn profiles associated with the email address '{request.email}'.\n"
        
    if request.github_url:
        instruction += f"2. Go to their GitHub profile at: {request.github_url} (or the one you found). Read their pinned repositories, commit activity graph, and language breakdown.\n"
    else:
        instruction += "2. Once you find their GitHub profile, read their pinned repositories, commit activity graph, and language breakdown.\n"
        
    if request.linkedin_url:
        instruction += f"3. If possible, browse their LinkedIn profile at: {request.linkedin_url} (or the one you found) to extract their recent work experience and titles. Note that LinkedIn may block you; if so, skip this step.\n"
    else:
        instruction += "3. If possible, browse the LinkedIn profile you found to extract their recent work experience. Note that LinkedIn may block you; if so, skip this step.\n"
        
    instruction += (
        "4. Synthesize your findings into a structured JSON summary containing: \n"
        "   - 'candidate_name': string\n"
        "   - 'estimated_seniority': (e.g., Junior, Mid, Senior, Lead)\n"
        "   - 'top_skills': list of string\n"
        "   - 'key_projects': list of object {name, description}\n"
        "   - 'overall_assessment': concise paragraph of your professional evaluation.\n"
        "Please output only valid JSON."
    )
    
    try:
        async with AsyncOpenClaw.remote(api_key=api_key) as client:
            logger.info(f"Triggering candidate analysis for {request.candidate_name}")
            
            if hasattr(client, 'agent'):
                # Pass the instruction to the agent
                result = await client.agent.run(instruction)
                
                return {
                    "status": "success",
                    "candidate_name": request.candidate_name,
                    "agent_analysis": str(result)
                }
            else:
                return {
                    "status": "pending",
                    "message": "Agent attribute missing on client. Analysis failed to trigger.",
                    "instruction_used": instruction
                }
                
    except Exception as e:
        logger.error(f"Failed to perform candidate analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=Dict[str, Any])
async def chat_with_admin(
    chat_request: ChatRequest,
    fastapi_request: Request,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_session)
):
    """
    Universal API Agent Chatbot.
    The agent is provided with an overview of the platform's APIs and can 
    dynamically construct JSON commands to call them.
    """
    api_key = os.getenv("OPENCLAW_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENCLAW_API_KEY environment variable is not configured.")

    # High-level API documentation injected into the agent's context
    api_docs = (
        "You are the 'Interview Platform Administrator'. You have a Universal API Calling Tool.\n"
        "Your goal is to help the admin manage the platform by calling any necessary API endpoints.\n\n"
        "AVAILABLE API OVERVIEW:\n"
        "1. USERS: \n"
        "   - GET /api/admin/users (List/Search candidates)\n"
        "   - POST /api/admin/users/create (Create new user/candidate)\n"
        "   - GET /api/admin/users/{id} (Get full user details, including resume_path)\n"
        "2. INTERVIEWS: \n"
        "   - POST /api/admin/interviews/schedule (Schedule an interview)\n"
        "   - GET /api/admin/interviews (List all scheduled sessions)\n"
        "3. QUESTION PAPERS: \n"
        "   - GET /api/admin/papers (List standard MCQ papers)\n"
        "   - GET /api/admin/coding-papers (List coding papers)\n"
        "4. DASHBOARD: \n"
        "   - GET /api/admin/dashboard/summary (Get overall platform stats)\n\n"
        "HOW TO EXECUTE ACTIONS:\n"
        "If the admin's request requires an API call, you MUST output a JSON block in this exact format:\n"
        "```json\n"
        '{\n'
        '  "action": "call_api",\n'
        '  "method": "GET | POST | PUT | DELETE",\n'
        '  "endpoint": "/api/admin/...",\n'
        '  "body": {}, \n'
        '  "params": {} \n'
        '}\n'
        "```\n"
        "Respond conversationally AFTER the tool output. If info is missing, ask for it first."
    )

    try:
        async with AsyncOpenClaw.remote(api_key=api_key) as client:
            full_prompt = f"{api_docs}\n\nAdmin Message:\n{chat_request.message}"
            
            if hasattr(client, 'agent'):
                response_text = await client.agent.run(full_prompt)
                
                # Intercept Universal API Call
                if "call_api" in str(response_text) and "{" in str(response_text):
                    try:
                        json_match = re.search(r'\{.*\}', str(response_text), re.DOTALL)
                        if json_match:
                            command = json.loads(json_match.group())
                            
                            if command.get("action") == "call_api":
                                method = command.get("method", "GET").upper()
                                endpoint = command.get("endpoint")
                                body = command.get("body", {})
                                params = command.get("params", {})
                                
                                # --- PRODUCTION RESILIENCE UPDATE ---
                                # Instead of calling http://localhost:8000 (which can fail in complex production networks),
                                # we use httpx.AsyncClient(app=fastapi_request.app).
                                # This allows httpx to communicate DIRECTLY with the FastAPI application in memory,
                                # bypassing the network layer entirely. This is 100% reliable in Docker, Cloud, etc.
                                base_url = "http://internal.api" 
                                
                                # We forward the Admin's JWT token for secure internal authentication
                                auth_header = fastapi_request.headers.get("Authorization")
                                headers = {"Authorization": auth_header} if auth_header else {}

                                # Correct syntax for calling internal ASGI app in newer httpx versions
                                transport = httpx.ASGITransport(app=fastapi_request.app)
                                async with httpx.AsyncClient(transport=transport, base_url=base_url) as http_client:
                                    logger.info(f"Agent triggered internal API: {method} {endpoint}")
                                    
                                    api_response = await http_client.request(
                                        method=method,
                                        url=f"{base_url}{endpoint}",
                                        json=body if method in ["POST", "PUT"] else None,
                                        params=params,
                                        headers=headers,
                                        timeout=30.0
                                    )
                                    
                                    # Feed the API response back to the Agent for a natural summary
                                    second_prompt = (
                                        f"The API returned: {api_response.status_code} - {api_response.text}\n"
                                        "Please explain this result to the admin in a friendly conversational way."
                                    )
                                    final_reply = await client.agent.run(second_prompt)
                                    
                                    return {
                                        "reply": str(final_reply),
                                        "api_called": f"{method} {endpoint}",
                                        "api_status": api_response.status_code
                                    }
                    except Exception as e:
                        logger.error(f"Universal Tool execution failed: {e}")
                        return {"reply": f"I tried to call the API, but something went wrong: {str(e)}", "action_taken": False}

                return {
                    "reply": str(response_text).replace("```json", "").replace("```", "").strip(),
                    "action_taken": False
                }
            else:
                return {"reply": "Agent SDK not fully initialized.", "action_taken": False}
                
    except Exception as e:
        logger.error(f"Chat execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
