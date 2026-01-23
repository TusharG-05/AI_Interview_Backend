import os
import fitz  # PyMuPDF
import re
from docx import Document
from sentence_transformers import SentenceTransformer, util
import torch

class NLPService:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        print(f"Initializing NLPService (Lazy Loading)...")
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        if self._model is None:
            print(f"Loading NLP Model ({self.model_name})...")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def calculate_similarity(self, text1, text2):
        """Calculates semantic similarity between two strings."""
        if not text1 or not text2:
            return 0.0
        
        embeddings1 = self.model.encode(text1, convert_to_tensor=True)
        embeddings2 = self.model.encode(text2, convert_to_tensor=True)
        
        cosine_score = util.cos_sim(embeddings1, embeddings2)
        return float(cosine_score[0][0])

    def extract_qa_from_file(self, file_path):
        """Extracts Q&A pairs from .txt, .pdf, or .docx files."""
        ext = os.path.splitext(file_path)[1].lower()
        content = ""

        try:
            if ext == '.txt':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            elif ext == '.pdf':
                doc = fitz.open(file_path)
                content = "\n".join([page.get_text() for page in doc])
                doc.close()
            elif ext == '.docx':
                doc = Document(file_path)
                content = "\n".join([para.text for para in doc.paragraphs])
            else:
                raise ValueError(f"Unsupported file format: {ext}")
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return []

        # Debug: Print first 500 chars to see what was extracted
        print(f"--- DOCUMENT CONTENT PREVIEW ({ext}) ---")
        print(content[:500])
        print("---------------------------------------")

        return self.parse_qa_pairs(content)

    def parse_qa_pairs(self, text):
        """
        Regex-based parser to find Question and Answer patterns.
        Handles diverse labels and multi-line content.
        """
        # Clean text of some common non-printable PDF artifacts
        text = "".join(char for char in text if char.isprintable() or char in "\n\r\t")
        
        # Patterns for questions and answers
        # Looking for start of line with markers like Q:, 1., Question: etc.
        # Allowing optional space before the marker
        q_pattern = re.compile(r'^\s*(?:Q:|Question:|Ques:|Q\s*:|Question\s*:|\d+[\.\)])\s*(.*)', re.IGNORECASE)
        a_pattern = re.compile(r'^\s*(?:A:|Answer:|Ans:|Reference:|A\s*:|Answer\s*:)\s*(.*)', re.IGNORECASE)

        lines = text.split('\n')
        qa_pairs = []
        current_q = None
        current_a = None

        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            q_match = q_pattern.match(line)
            if q_match:
                # If we were already building a pair, save it
                if current_q and current_a:
                    qa_pairs.append({'question': current_q.strip(), 'answer': current_a.strip()})
                    current_a = None
                current_q = q_match.group(1)
                continue

            a_match = a_pattern.match(line)
            if a_match:
                current_a = a_match.group(1)
                continue

            # Continuation of previous line
            if current_a is not None:
                current_a += " " + line
            elif current_q is not None:
                current_q += " " + line

        # Add the final pair
        if current_q and current_a:
            qa_pairs.append({'question': current_q.strip(), 'answer': current_a.strip()})

        print(f"Extraction result: Found {len(qa_pairs)} pairs.")
        return qa_pairs
