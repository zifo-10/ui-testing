from io import BytesIO

from docx import Document
import re


def read_docx(file_content: BytesIO):
    try:
        doc = Document(file_content)
        full_text = []

        for para in doc.paragraphs:
            full_text.append(para.text)

        # Join all paragraphs into one large string
        content = '\n'.join(full_text)

        # Split content based on "المقطع" at the start of each new section
        sections = re.split(r'^\s*Video\s+\S+', content, flags=re.MULTILINE)

        # Clean up sections by removing any leading/trailing whitespace
        sections = [s.strip() for s in sections if s.strip()]

        return sections

    except Exception as e:
        return f"Error reading .docx file: {e}"
