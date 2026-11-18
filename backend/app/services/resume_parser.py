import re
from typing import List, Optional

from ..schemas import CandidateProfile
from .jd_parser import find_skills

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?:\+?\d[\d()\-\.\s]{7,}\d)")


def _extract_name(lines: List[str]) -> str:
    for line in lines[:12]:
        candidate = re.sub(r"^[\-•*\d\s]+", "", line).strip()
        if not candidate:
            continue
        if len(candidate.split()) > 6:
            continue
        lowered = candidate.lower()
        if any(token in lowered for token in ["email", "phone", "skills", "experience", "education", "profile", "summary"]):
            continue
        if re.fullmatch(r"[\d\s\-/]+", candidate):
            continue
        return candidate
    return "Candidate"


def _extract_email(text: str) -> Optional[str]:
    match = EMAIL_RE.search(text)
    return match.group(0).strip() if match else None


def _extract_phone(text: str) -> Optional[str]:
    matches = PHONE_RE.findall(text)
    for value in matches:
        cleaned = re.sub(r"\s+", " ", value).strip()
        if len(re.sub(r"\D", "", cleaned)) >= 8:
            return cleaned
    return None


def _extract_summary(lines: List[str]) -> str:
    parts: List[str] = []
    for line in lines[1:20]:
        clean = line.strip()
        if not clean:
            continue
        lowered = clean.lower()
        if any(token in lowered for token in ["skills", "experience", "education", "contact", "phone", "email"]):
            continue
        if len(clean.split()) > 18:
            continue
        parts.append(clean)
        if len(parts) >= 2:
            break
    return " ".join(parts).strip() or "Resume profile extracted from uploaded document."


def _extract_experience_years(text: str) -> Optional[float]:
    patterns = [
        r"(\d+(?:\.\d+)?)\s*(?:\+|plus)\s*(?:years?|yrs?)",
        r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        r"(?:for\s+)?(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s*(?:of\s+experience)",
    ]
    values: List[float] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.I):
            if match.lastindex:
                groups = [g for g in match.groups() if g is not None]
                if len(groups) == 2:
                    values.extend([float(groups[0]), float(groups[1])])
                else:
                    values.append(float(groups[0]))
    if not values:
        return None
    return max(values)


def _extract_education(lines: List[str]) -> List[str]:
    education: List[str] = []
    for line in lines:
        lower = line.lower()
        if any(token in lower for token in ["bachelor", "master", "phd", "diploma", "degree", "graduation", "b.tech", "m.tech"]):
            clean = line.strip()
            if clean not in education:
                education.append(clean)
    return education[:5]


def parse_resume_text(text: str) -> CandidateProfile:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = _extract_name(lines)
    email = _extract_email(text)
    phone = _extract_phone(text)
    summary = _extract_summary(lines)
    skills = find_skills(text)
    experience_years = _extract_experience_years(text)
    if experience_years is None:
        experience_years = 0.0
    education = _extract_education(lines)

    return CandidateProfile(
        name=name,
        email=email,
        phone=phone,
        skills=skills,
        experience_years=experience_years,
        education=education,
        summary=summary,
        raw_text=text,
    )
