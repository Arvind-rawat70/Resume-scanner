import io

from docx import Document
from fastapi.testclient import TestClient

from app.main import app
from app.services.resume_parser import parse_resume_text
from app.services.text_extract import extract_text
from app.services.resume_match import score_resume_against_jd


def _make_docx_bytes(text: str) -> bytes:
    doc = Document()
    doc.add_paragraph(text)
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def _make_pdf_bytes(text: str) -> bytes:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length 57 >>\nstream\nBT\n/F1 16 Tf\n50 100 Td\n("
        + escaped.encode("utf-8")
        + b") Tj\nET\nendstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000063 00000 n \n0000000128 00000 n \n0000000259 00000 n \n0000000567 00000 n \ntrailer\n<< /Root 1 0 R /Size 6 >>\nstartxref\n643\n%%EOF"
    )
    return pdf


def test_parse_resume_text_extracts_candidate_profile():
    resume = """
    John Doe
    john.doe@email.com | +1 415 555 1234
    Senior Backend Engineer

    Profile:
    Experienced backend engineer with 5+ years building APIs in Python, FastAPI, PostgreSQL, and React.

    Skills: Python, FastAPI, PostgreSQL, React, Docker, AWS

    Experience
    - Built REST APIs for fintech platform using Python, FastAPI and PostgreSQL.
    - Led frontend work in React for internal dashboards.

    Education
    Bachelor's in Computer Science, 2020
    """

    profile = parse_resume_text(resume)
    assert profile.name == "John Doe"
    assert profile.email == "john.doe@email.com"
    assert profile.phone == "+1 415 555 1234"
    assert {"Python", "FastAPI", "PostgreSQL", "React"}.issubset(set(profile.skills))
    assert profile.experience_years >= 5
    assert profile.education
    assert "Computer Science" in " ".join(profile.education)


def test_supported_resume_formats_can_be_extracted():
    docx_bytes = _make_docx_bytes("Alice Johnson\nPython, React, PostgreSQL\n")
    pdf_bytes = _make_pdf_bytes("Alice Johnson\nPython, React, PostgreSQL\n")

    docx_text, _ = extract_text("resume.docx", docx_bytes)
    pdf_text, _ = extract_text("resume.pdf", pdf_bytes)

    assert "Alice Johnson" in docx_text
    assert "Python" in pdf_text


def test_resume_without_experience_is_treated_as_fresher():
    resume = "Alice Johnson\nPython, React, PostgreSQL\n"
    profile = parse_resume_text(resume)
    assert profile.experience_years == 0.0


def test_resume_batch_upload_endpoint_accepts_multiple_files():
    client = TestClient(app)
    content = "Alice Johnson\nalice.johnson@example.com\nFull Stack Developer\n\nSkills: Python, JavaScript, React, PostgreSQL\n"
    files = [
        ("files", ("resume1.docx", _make_docx_bytes(content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
        ("files", ("resume2.pdf", _make_pdf_bytes(content), "application/pdf")),
    ]

    response = client.post("/api/resumes/upload", files=files)
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2
    assert len(payload["candidates"]) == 2
    assert payload["candidates"][0]["name"]


def test_score_resume_against_jd_includes_semantic_and_missing_skills():
    jd = {
        "title": "Python Backend Engineer",
        "summary": "Backend engineer with Python, FastAPI, PostgreSQL, and Docker.",
        "skills": [
            {"name": "Python", "category": "Language", "importance": "required", "evidence": "Python"},
            {"name": "FastAPI", "category": "Framework", "importance": "required", "evidence": "FastAPI"},
            {"name": "PostgreSQL", "category": "Database", "importance": "required", "evidence": "PostgreSQL"},
            {"name": "Docker", "category": "DevOps", "importance": "preferred", "evidence": "Docker"},
            {"name": "Kafka", "category": "Messaging", "importance": "preferred", "evidence": "Kafka"},
        ],
        "experience": {"min_years": 3, "max_years": None, "raw_text": "3+ years", "seniority": "Mid"},
        "education": [],
        "certifications": [],
        "responsibilities": [],
        "soft_skills": [],
        "word_count": 50,
    }
    candidate = {
        "name": "Alice",
        "email": "alice@example.com",
        "phone": None,
        "skills": ["Python", "FastAPI", "PostgreSQL", "React"],
        "experience_years": 5,
        "education": ["Bachelor's in Computer Science"],
        "summary": "Experienced backend engineer with Python, FastAPI and PostgreSQL experience in production systems.",
        "raw_text": "Experienced backend engineer with Python, FastAPI and PostgreSQL experience in production systems.",
    }

    result = score_resume_against_jd(jd, candidate)

    assert result["overall_score"] >= 75
    assert set(result["matched_skills"]) >= {"Python", "FastAPI", "PostgreSQL"}
    assert "Kafka" in result["missing_skills"]
    assert result["experience_match_score"] > 0.8
    assert result["semantic_similarity"] > 0.5
    assert "reasons" in result and result["reasons"]


def test_match_resume_api_returns_score_breakdown():
    client = TestClient(app)
    jd = {
        "title": "Senior Python Engineer",
        "summary": "Python backend engineer with FastAPI and PostgreSQL",
        "skills": [
            {"name": "Python", "category": "Language", "importance": "required", "evidence": "Python"},
            {"name": "FastAPI", "category": "Framework", "importance": "required", "evidence": "FastAPI"},
            {"name": "PostgreSQL", "category": "Database", "importance": "required", "evidence": "PostgreSQL"},
            {"name": "Docker", "category": "DevOps", "importance": "preferred", "evidence": "Docker"},
        ],
        "experience": {"min_years": 4, "max_years": None, "raw_text": "4+ years", "seniority": "Senior"},
        "education": [],
        "certifications": [],
        "responsibilities": [],
        "soft_skills": [],
        "word_count": 30,
    }
    payload = {
        "jd": jd,
        "candidates": [{
            "name": "Alice",
            "email": "alice@example.com",
            "skills": ["Python", "FastAPI", "PostgreSQL", "React"],
            "experience_years": 6,
            "education": ["Bachelor's in CS"],
            "summary": "Python, FastAPI, PostgreSQL backend developer.",
            "raw_text": "Python, FastAPI, PostgreSQL backend developer.",
        }],
    }

    response = client.post("/api/match/resumes", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["results"][0]["overall_score"] >= 70
    assert "matched_skills" in data["results"][0]
    assert "missing_skills" in data["results"][0]
