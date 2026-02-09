"""
Modal.com app for GPU-accelerated LLM evaluation using Llama 3 8B.

Deploy: modal deploy app/modal_llm.py
Test:   modal run app/modal_llm.py --question "What is Python?" --answer "A programming language"
"""
import modal

app = modal.App("interview-llm-eval")

# Container image with vllm for fast inference
llm_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("vllm==0.6.6", "transformers", "torch")
)

# Download model at container build time
MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"

SYSTEM_PROMPT = """You are an expert technical interviewer. Evaluate the candidate's answer and provide constructive feedback.

You must return your response in valid JSON format with exactly two keys:
- "feedback": A string with detailed, constructive feedback
- "score": A float between 0 and 10

Do not include any text outside the JSON object."""


@app.cls(
    image=llm_image,
    gpu="A10G",  # 24GB VRAM - good for Llama 3 8B
    timeout=120,
    secrets=[modal.Secret.from_name("huggingface-secret")],
    container_idle_timeout=300,  # Keep warm for 5 mins
)
class LLMEvaluator:
    @modal.enter()
    def load_model(self):
        """Load model once when container starts."""
        from vllm import LLM, SamplingParams
        
        self.llm = LLM(
            model=MODEL_ID,
            trust_remote_code=True,
            max_model_len=4096,
        )
        self.sampling_params = SamplingParams(
            temperature=0.1,
            max_tokens=512,
            stop=["```", "\n\n\n"]
        )
    
    @modal.method()
    def evaluate(self, question: str, answer: str) -> dict:
        """Evaluate an interview answer and return feedback + score."""
        import json
        
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
{SYSTEM_PROMPT}<|eot_id|><|start_header_id|>user<|end_header_id|>
Question: {question}

Candidate's Answer: {answer}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
        
        outputs = self.llm.generate([prompt], self.sampling_params)
        response_text = outputs[0].outputs[0].text.strip()
        
        # Clean markdown if present
        if response_text.startswith("```"):
            lines = response_text.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = "\n".join(lines).strip()
        
        try:
            result = json.loads(response_text)
            if "feedback" not in result:
                result["feedback"] = response_text
            if "score" not in result:
                result["score"] = 5.0
            return result
        except json.JSONDecodeError:
            return {
                "feedback": response_text,
                "score": 5.0
            }


@app.local_entrypoint()
def main(question: str = "What is a Python decorator?", answer: str = "It's a function that modifies another function."):
    """CLI test: modal run app/modal_llm.py"""
    evaluator = LLMEvaluator()
    result = evaluator.evaluate.remote(question, answer)
    print(f"Feedback: {result['feedback']}")
    print(f"Score: {result['score']}/10")
