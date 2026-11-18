from typing import List, Optional
from pydantic import BaseModel


class SkillRequirement(BaseModel):
    name: str            # canonical name, e.g. "Spring Boot"
    category: str        # e.g. "Backend Framework"
    importance: str      # "required" | "preferred"
    evidence: str        # the sentence that mentioned it (explainability)


class ExperienceRequirement(BaseModel):
    min_years: Optional[float] = None
    max_years: Optional[float] = None
    raw_text: Optional[str] = None
    seniority: Optional[str] = None   # junior / mid / senior / lead ...


class EducationRequirement(BaseModel):
    level: str                 # Bachelor's / Master's / PhD / Diploma
    fields: List[str] = []
    required: bool = True
    raw_text: str = ""


class ParsedJD(BaseModel):
    title: Optional[str]
    summary: str
    skills: List[SkillRequirement]
    experience: ExperienceRequirement
    education: List[EducationRequirement]
    certifications: List[str]
    responsibilities: List[str]
    soft_skills: List[str]
    word_count: int


class CandidateProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = []
    experience_years: Optional[float] = None
    education: List[str] = []
    summary: str = ""
    raw_text: str = ""
