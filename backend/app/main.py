from typing import List

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .schemas import CandidateProfile, ParsedJD
from .services.jd_parser import parse_job_description
from .services.resume_match import score_resume_against_jd
from .services.resume_parser import parse_resume_text
from .services.semantic_match import semantic_similarity
from .services.text_extract import EmptyDocument, UnsupportedFileType, extract_text

MAX_BYTES = 5 * 1024 * 1024

app = FastAPI(title="Resume Matcher API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/jd/parse", response_model=ParsedJD)
async def parse_jd(text: str = Form(None), file: UploadFile = File(None)):
    """Module 1. Accepts pasted text OR an uploaded PDF/DOCX/TXT file."""
    if file is not None and file.filename:
        data = await file.read()
        if len(data) > MAX_BYTES:
            raise HTTPException(413, "File too large (max 5 MB).")
        try:
            text, _ = extract_text(file.filename, data)
        except UnsupportedFileType as e:
            raise HTTPException(415, str(e))
        except EmptyDocument as e:
            raise HTTPException(422, str(e))
        except Exception:
            raise HTTPException(422, "Could not read this file. It may be corrupted or password-protected.")
    if not text or len(text.strip()) < 40:
        raise HTTPException(422, "Paste or upload a job description (at least a couple of sentences).")
    return parse_job_description(text)


@app.post("/api/match/semantic")
async def semantic_match(request: Request, job_description: str = Form(None), candidate_text: str = Form(None)):
    """Module 3: semantic similarity between a JD and a resume description."""
    if job_description is None or candidate_text is None:
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        job_description = payload.get("job_description", job_description)
        candidate_text = payload.get("candidate_text", candidate_text)

    if not job_description or not candidate_text or not str(job_description).strip() or not str(candidate_text).strip():
        raise HTTPException(422, "Both job_description and candidate_text are required.")

    score = semantic_similarity(job_description, candidate_text)
    return {
        "score": round(float(score), 4),
        "label": "strong" if score >= 0.7 else "moderate" if score >= 0.45 else "low",
    }


@app.post("/api/resumes/upload")
async def upload_resumes(files: List[UploadFile] = File(...)):
    """Module 2: batch upload of PDFs and DOCX resumes. Returns extracted candidate data."""
    if not files:
        raise HTTPException(422, "Upload at least one resume file.")

    candidates = []
    for upload in files:
        if not upload.filename:
            continue
        data = await upload.read()
        if len(data) > MAX_BYTES:
            raise HTTPException(413, f"File too large: {upload.filename}")
        try:
            text, _ = extract_text(upload.filename, data)
        except UnsupportedFileType as e:
            raise HTTPException(415, f"{upload.filename}: {str(e)}")
        except EmptyDocument as e:
            raise HTTPException(422, f"{upload.filename}: {str(e)}")
        except Exception:
            raise HTTPException(422, f"Could not read {upload.filename}. It may be corrupted or password-protected.")

        profile = parse_resume_text(text)
        candidate = CandidateProfile(**profile.model_dump())
        candidates.append({
            "filename": upload.filename,
            "name": candidate.name,
            "email": candidate.email,
            "phone": candidate.phone,
            "skills": candidate.skills,
            "experience_years": candidate.experience_years,
            "education": candidate.education,
            "summary": candidate.summary,
        })

    return {"count": len(candidates), "candidates": candidates}


@app.post("/api/match/resumes")
async def match_resumes(request: Request):
    """Module 3: score every uploaded candidate against the parsed JD."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(422, "Request body must be valid JSON.")

    if not payload:
        raise HTTPException(422, "JSON payload is required.")

    jd_data = payload.get("jd")
    candidates = payload.get("candidates", [])
    if jd_data is None:
        job_description = payload.get("job_description")
        if job_description:
            jd_data = parse_job_description(job_description).model_dump()
        else:
            raise HTTPException(422, "A job description or parsed JD is required.")

    if not isinstance(candidates, list) or not candidates:
        raise HTTPException(422, "At least one candidate profile is required.")

    jd = parse_job_description(jd_data["summary"]) if isinstance(jd_data, dict) and "summary" in jd_data and "skills" not in jd_data else jd_data
    if isinstance(jd, dict) and "skills" in jd:
        jd_obj = jd
    else:
        jd_obj = parse_job_description(jd if isinstance(jd, str) else str(jd)).model_dump()

    results = []
    for candidate in candidates:
        result = score_resume_against_jd(jd_obj, candidate)
        result["candidate_name"] = candidate.get("name", "Candidate")
        result["candidate_email"] = candidate.get("email")
        results.append(result)

    ordered = sorted(results, key=lambda item: item["overall_score"], reverse=True)
    return {"count": len(ordered), "results": ordered}
