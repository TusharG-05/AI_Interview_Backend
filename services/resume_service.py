import fitz
from fastapi import UploadFile

async def extract_text_from_pdf(resume: UploadFile) -> str:
    extracted_text = ""
    if resume.filename.endswith('.pdf'):
        pdf_content = await resume.read()
        with fitz.open(stream=pdf_content, filetype="pdf") as doc:
            for page in doc:
                extracted_text += page.get_text()
    return extracted_text
