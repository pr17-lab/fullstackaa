import asyncio
import io
from fastapi.testclient import TestClient
from PyPDF2 import PdfWriter, PdfReader
from app.main import app
from app.api.dependencies.auth import get_current_user
from app.models.user import User

# Create a mock user
mock_user = User(
    id="00000000-0000-0000-0000-000000000000",
    email="test@example.com",
)

app.dependency_overrides[get_current_user] = lambda: mock_user

client = TestClient(app)

def create_sample_pdf():
    writer = PdfWriter()
    page = writer.add_blank_page(width=72, height=72)
    # Just a simple pdf, inserting text into it using pure python is complex without ReportLab
    # So we'll just write one and see if backend handles it without crashing
    
    # Actually wait, PyPDF2 does not easily create PDFs with text.
    pass

import os

def test_parse_pdf():
    # Write a simple PDF with reportlab, or if reportlab not installed, just test error handling
    try:
        from reportlab.pdfgen import canvas
        pdf_bytes = io.BytesIO()
        c = canvas.Canvas(pdf_bytes)
        c.drawString(100, 100, "Hello World from PDF Resume!")
        c.save()
        pdf_content = pdf_bytes.getvalue()
    except ImportError:
        print("ReportLab not installed, just sending empty PDF from PyPDF2")
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        pdf_bytes = io.BytesIO()
        writer.write(pdf_bytes)
        pdf_content = pdf_bytes.getvalue()

    response = client.post(
        "/api/interview/sessions/parse-resume",
        files={"file": ("test_resume.pdf", pdf_content, "application/pdf")}
    )
    print("Status:", response.status_code)
    print("JSON:", response.json())

if __name__ == "__main__":
    test_parse_pdf()
