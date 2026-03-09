import asyncio
import os
from app.services.interview import evaluate_answer_content

def test_groq_evaluation():
    print(f"\n🚀 Testing Evaluation Logic with GROQ_API_KEY: {'[SET]' if os.getenv('GROQ_API_KEY') else '[MISSING]'}")
    
    # Simulate a standard technical interview question
    question = "Explain the difference between a list and a tuple in Python."
    answer = "A list is mutable, meaning it can be changed after creation, using square brackets. A tuple is immutable, meaning it cannot be changed, and uses parentheses. Tuples are generally faster and safer for fixed data."
    
    print("\nSimulating Question:")
    print(f"Q: {question}")
    print(f"A: {answer}")
    
    print("\nCalling evaluate_answer_content()...")
    # This should hit the Groq fallback logic since USE_MODAL is false
    result = evaluate_answer_content(question, answer)
    
    print("\n--- Result ---")
    print(f"Score: {result.get('score')}")
    print(f"Feedback: {result.get('feedback')}")
    print("--------------\n")
    
    if result.get('score') is not None and result.get('feedback'):
        print("✅ Groq Evaluation Parsing SUCCESS")
    else:
        print("🔴 Groq Evaluation Parsing FAILED")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test_groq_evaluation()
