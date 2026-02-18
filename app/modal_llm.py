"""
Modal.com app for GPU-accelerated LLM evaluation using Llama 3 8B.

Deploy: modal deploy app/modal_llm.py
Test:   modal run app/modal_llm.py --question "What is Python?" --answer "A programming language"
"""
import modal

app = modal.App("interview-llm-eval")

# Container image with vllm for fast inference
# Using a more robust CUDA-enabled base image
def download_model():
    from huggingface_hub import snapshot_download
    
    # Ensure HF_TOKEN is set for the download
    # The secret is injected into this function's environment
    print(f"📦 Building Image: Downloading {MODEL_ID}...")
    try:
        snapshot_download(MODEL_ID)
        print(f"✅ Download complete!")
    except Exception as e:
        print(f"❌ Download failed: {e}")
        raise

llm_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("vllm==0.6.6", "transformers==4.45.2", "torch", "huggingface_hub")
    # Bake the model into the image
    .run_function(download_model, secrets=[modal.Secret.from_name("huggingface-secret")])
)

# Download model at container build time
MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"

SYSTEM_PROMPT = """You are an expert technical interviewer. Evaluate the candidate's answer and provide constructive feedback.

You must return your response in valid JSON format with exactly two keys:
- "feedback": A string with detailed, constructive feedback
- "score": A float between 0 and 10

Do not include any text outside the JSON object."""


@app.cls(
    image=llm_image,
    gpu="A10G",  # 24GB VRAM - good for Llama 3 8B
    timeout=600, # Increased timeout for model download/load
    secrets=[modal.Secret.from_name("huggingface-secret")],
    enable_memory_snapshot=True,
    scaledown_window=300,  # Updated from container_idle_timeout
)
class LLMEvaluator:
    @modal.enter()
    def load_model(self):
        """Load model once when container starts."""
        import sys
        import os
        import time
        import traceback

        print("🚀 Modal Container: Starting load_model phase...", flush=True)
        try:
            # 1. Debug Environment
            print(f"DEBUG: Python {sys.version}", flush=True)
            print(f"DEBUG: Current Working Directory: {os.getcwd()}", flush=True)
            
            # Check Secrets
            hb_token = os.environ.get("HUGGING_FACE_HUB_TOKEN")
            hf_token = os.environ.get("HF_TOKEN")
            
            if hb_token:
                print(f"✅ Found HUGGING_FACE_HUB_TOKEN (prefix: {hb_token[:4]}...)", flush=True)
                os.environ["HF_TOKEN"] = hb_token
            elif hf_token:
                print(f"✅ Found HF_TOKEN (prefix: {hf_token[:4]}...)", flush=True)
            else:
                print("⚠️ WARNING: No Hugging Face token found in environment variables!", flush=True)

            # 2. Import vLLM (Can crash if dependencies missing)
            print("📦 Importing vLLM...", flush=True)
            try:
                from vllm import LLM, SamplingParams
                print("✅ vLLM imported successfully.", flush=True)
            except ImportError as e:
                print(f"❌ Critical ImportError: {e}", flush=True)
                raise

            # 3. Load Model
            print(f"📦 Loading Model: {MODEL_ID}...", flush=True)
            print("   Config: max_model_len=2048, gpu_memory_utilization=0.75, enforce_eager=True", flush=True)
            
            start_time = time.time()
            self.llm = LLM(
                model=MODEL_ID,
                trust_remote_code=True,
                max_model_len=2048, 
                gpu_memory_utilization=0.75, # Slightly increased to ensuring enough but safe
                enforce_eager=True, 
                tensor_parallel_size=1 # Explicitly set to 1 for A10G single GPU
            )
            self.sampling_params = SamplingParams(
                temperature=0.1,
                max_tokens=512,
                stop=["```", "\n\n\n"]
            )
            elapsed = time.time() - start_time
            print(f"✨ Model Loaded Successfully in {elapsed:.2f}s!", flush=True)
            
        except Exception as e:
            print(f"❌ CRITICAL ERROR during load_model: {str(e)}", flush=True)
            traceback.print_exc()
            # We explicitly flush stderr too
            sys.stderr.flush()
            sys.stdout.flush()
            raise # Re-raise to ensure Modal sees the failure
    
    @modal.method()
    def evaluate(self, question: str, answer: str) -> dict:
        """Evaluate an interview answer and return feedback + score."""
        import json
        
        # Qwen 2.5 uses ChatML format
        prompt = f"""<|im_start|>system
{SYSTEM_PROMPT}
<|im_end|>
<|im_start|>user
Question: {question}

Candidate's Answer: {answer}
<|im_end|>
<|im_start|>assistant
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
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    evaluator = LLMEvaluator()
    result = evaluator.evaluate.remote(question, answer)
    logger.info(f"Feedback: {result['feedback']}")
    logger.info(f"Score: {result['score']}/10")
