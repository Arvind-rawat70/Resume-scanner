"""
Module 1: Job Description parser.

Rule-based + taxonomy extraction. Deliberately transparent so every extracted
item carries the sentence it came from ("evidence"). Module 3 reuses the output
(skills split into required/preferred, years, education) as the matching target.

Pipeline
  1. split text into lines, detect section headers (requirements / preferred / ...)
  2. per line: find skills via word-boundary alias matching
  3. importance = section header, overridden by wording cues ("nice to have", ...)
  4. regex extraction for years of experience, education, certifications
"""
import re
from typing import Dict, List, Optional, Tuple

from ..schemas import (EducationRequirement, ExperienceRequirement, ParsedJD,
                       SkillRequirement)
from .skills_taxonomy import (ALIAS_TO_CANONICAL, CATEGORY, SOFT_SKILLS,
                              SUBSUMES)

# ---------- section detection ----------
SECTION_KEYWORDS: List[Tuple[str, List[str]]] = [
    # order matters: "preferred qualifications" must hit preferred before required
    ("preferred", ["preferred", "nice to have", "nice-to-have", "good to have",
                   "bonus", "desirable", "plus points", "added advantage", "great to have",
                   "following is preferred", "preferred stack", "preferred technologies"]),
    ("ignore", ["benefits", "perks", "what we offer", "compensation", "salary",
                "about us", "about the company", "who we are", "equal opportunity",
                "how to apply", "why join"]),
    ("responsibilities", ["responsibilities", "what you'll do", "what you will do",
                          "what you’ll do", "duties", "your role", "the role",
                          "day to day", "key tasks"]),
    ("required", ["requirements", "required", "qualifications", "must have",
                  "must-have", "what you bring", "what we're looking for",
                  "what we’re looking for", "who you are", "skills", "you have",
                  "minimum"]),
]

PREFERRED_CUES = re.compile(
    r"\b(nice to have|nice-to-have|good to have|preferred|bonus|a plus|is a plus|"
    r"plus point|added advantage|desirable|familiarity with|exposure to|"
    r"would be an advantage|an advantage|ideally)\b", re.I)

BULLET = re.compile(r"^\s*(?:[-•*▪◦·–]|\d+[.)])\s+")


def _header_kind(line: str) -> Optional[str]:
    clean = re.sub(r"[*#_:]", "", line).strip().lower()
    if not clean:
        return None
    if BULLET.match(line):
        return None
    # Allow longer preferred-intro lines like "Candidates can choose their own stack, but the following is preferred:"
    for kind, kws in SECTION_KEYWORDS:
        if any(k in clean for k in kws):
            if kind == "preferred":
                return kind
            if len(clean) <= 60 or clean.endswith(":") or clean.endswith("-"):
                return kind
            return None
    return None


# ---------- skill matching ----------
def _skill_aliases_for_scanning() -> List[str]:
    """Longest aliases first so a specific skill wins over a shorter generic match.

    This also lets compact lists like "JavaNode.jsAWSMicroservices" be parsed, where
    the skills are adjacent and not separated by spaces.
    """
    return sorted(ALIAS_TO_CANONICAL.keys(), key=lambda alias: (-len(alias), alias.lower()))


def find_skills(text: str) -> List[str]:
    """Canonical skill names mentioned in `text`, in order, de-duplicated."""
    chosen: List[Tuple[int, int, str]] = []
    for alias in _skill_aliases_for_scanning():
        for m in re.finditer(re.escape(alias), text, flags=re.I):
            start, end = m.span()
            canon = ALIAS_TO_CANONICAL[alias.lower()]
            if any(start < prev_end and prev_start < end for prev_start, prev_end, _ in chosen):
                continue
            chosen.append((start, end, canon))

    ordered = sorted(chosen, key=lambda item: item[0])
    found: List[str] = []
    for _, _, canon in ordered:
        if canon not in found:
            found.append(canon)
    for specific, generic in SUBSUMES.items():
        if specific in found:
            found = [f for f in found if f not in generic]
    return found


# ---------- experience ----------
_NUM = r"(\d{1,2}(?:\.\d)?)"
YEARS_PATTERNS = [
    re.compile(rf"{_NUM}\s*(?:-|–|to)\s*{_NUM}\s*\+?\s*(?:years?|yrs?)", re.I),
    re.compile(rf"(?:minimum|min\.?|at least|over|more than)\s*(?:of\s*)?{_NUM}\s*\+?\s*(?:years?|yrs?)", re.I),
    re.compile(rf"{_NUM}\s*\+?\s*(?:years?|yrs?)", re.I),
]
SENIORITY = [
    ("Intern", r"\bintern(ship)?\b"), ("Fresher", r"\b(fresher|entry[- ]level|graduate)\b"),
    ("Junior", r"\b(junior|jr\.?)\b"), ("Lead", r"\b(lead|principal|staff|architect|head of)\b"),
    ("Senior", r"\b(senior|sr\.?)\b"), ("Mid", r"\b(mid[- ]level|intermediate)\b"),
]


def extract_experience(sentences: List[str], title: Optional[str]) -> ExperienceRequirement:
    candidates = []  # (min, max, raw, mentions_skill)
    for s in sentences:
        if not re.search(r"experience|exp\b|years", s, re.I):
            continue
        for pat in YEARS_PATTERNS:
            m = pat.search(s)
            if m:
                g = [x for x in m.groups() if x]
                lo = float(g[0]); hi = float(g[1]) if len(g) > 1 else None
                candidates.append((lo, hi, s.strip(), bool(find_skills(s))))
                break
    min_years = max_years = raw = None
    if candidates:
        # prefer a general statement ("5+ years of experience") over skill-specific ones
        general = [c for c in candidates if not c[3]] or candidates
        lo, hi, raw, _ = max(general, key=lambda c: c[0])
        min_years, max_years = lo, hi

    # Seniority priority: job title > years of experience > opening lines of the JD.
    # (Body text like "mentor junior engineers" must not decide the level.)
    seniority = next((n for n, pat in SENIORITY if re.search(pat, title or "", re.I)), None)
    if not seniority and min_years is not None:
        seniority = "Junior" if min_years < 2 else "Mid" if min_years < 5 else "Senior"
    if not seniority:
        opening = " ".join(sentences[:3])
        seniority = next((n for n, pat in SENIORITY if re.search(pat, opening, re.I)), None)
    if not seniority:
        seniority = "Fresher"
    return ExperienceRequirement(min_years=min_years, max_years=max_years,
                                 raw_text=raw, seniority=seniority)


# ---------- education ----------
EDU_LEVELS = [
    ("PhD", r"\b(ph\.?d|doctorate|doctoral)\b"),
    ("Master's", r"\b(master'?s?|m\.?tech|m\.?sc|m\.?e\.?|mca|mba|ms)\b(?!\w)"),
    ("Bachelor's", r"\b(bachelor'?s?|b\.?tech|b\.?sc|b\.?e\.?|bca|bs|undergraduate|degree)\b"),
    ("Diploma", r"\bdiploma\b"),
]
EDU_FIELDS = ["Computer Science", "Information Technology", "Software Engineering",
              "Computer Engineering", "Engineering", "Mathematics", "Statistics",
              "Data Science", "Electronics", "Information Systems", "Business"]


def extract_education(sentences: List[str], preferred: set = frozenset()) -> List[EducationRequirement]:
    out: Dict[str, EducationRequirement] = {}
    for s in sentences:
        if not re.search(r"degree|bachelor|master|ph\.?d|diploma|b\.?tech|m\.?tech|b\.?e\b|mca|bca|graduat|education",
                         s, re.I):
            continue
        levels = [name for name, pat in EDU_LEVELS if re.search(pat, s, re.I)]
        if not levels:
            continue
        # a plain "degree" with other levels is just noise
        if len(levels) > 1 and "Bachelor's" in levels and not re.search(r"bachelor|b\.?tech|b\.?sc|bca|\bbs\b", s, re.I):
            levels.remove("Bachelor's")
        fields = [f for f in EDU_FIELDS if re.search(re.escape(f), s, re.I)]
        key = " / ".join(levels)
        if key not in out:
            out[key] = EducationRequirement(level=key, fields=fields,
                                            required=not (PREFERRED_CUES.search(s) or s in preferred),
                                            raw_text=s.strip())
    return list(out.values())


# ---------- certifications ----------
CERT_RE = re.compile(
    r"\b((?:AWS|Azure|Google|Oracle|Microsoft|Cisco|Red Hat)\s+Certified\s+[A-Z][\w\-]*(?:\s+[A-Z][\w\-]*){0,3}"
    r"|PMP|CISSP|CKAD|CKA|CSM|PSM|OCP|OCJP|Scrum Master|Six Sigma)\b")


def extract_certifications(text: str) -> List[str]:
    seen: List[str] = []
    for m in CERT_RE.finditer(text):
        c = m.group(1).strip()
        if c not in seen:
            seen.append(c)
    return seen


# ---------- misc ----------
def extract_title(lines: List[str]) -> Optional[str]:
    for l in lines[:15]:
        m = re.match(r"^\W*(?:job\s*title|position|role|designation)\s*[:\-–]\s*(.+)$", l, re.I)
        if m:
            return m.group(1).strip(" *#")
    for l in lines[:5]:
        clean = l.strip(" *#")
        if 2 <= len(clean.split()) <= 10 and not clean.endswith(".") and not _header_kind(l):
            return clean
    m = re.search(r"(?:hiring|looking for|seeking)\s+(?:an?\s+)?([A-Z][\w+/. -]{3,50}?)(?:\s+to\b|\s+who\b|\.|,)",
                  "\n".join(lines[:20]))
    return m.group(1).strip() if m else None


def extract_soft_skills(text: str) -> List[str]:
    low = text.lower()
    return [name for name, kws in SOFT_SKILLS.items() if any(k in low for k in kws)]


def _split_sentences(line: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z•\-])", line)
    return [p.strip() for p in parts if p.strip()]


def parse_job_description(text: str) -> ParsedJD:
    raw_lines = [l.rstrip() for l in text.split("\n")]
    lines = [l for l in raw_lines if l.strip()]
    title = extract_title(lines)

    section = "intro"
    skills: Dict[str, SkillRequirement] = {}
    responsibilities: List[str] = []
    sentences: List[str] = []          # content sentences used for experience/education
    preferred_sentences: set = set()   # sentences that sit under a "nice to have" header
    intro_lines: List[str] = []

    for idx, line in enumerate(lines):
        kind = _header_kind(line)
        if kind and not (idx == 0 and title and line.strip(" *#") == title):
            section = kind
            continue
        if section == "ignore":
            continue
        content = BULLET.sub("", line).strip()
        if section == "intro" and idx > 0 and len(content.split()) > 6:
            intro_lines.append(content)
        if section == "responsibilities" and len(responsibilities) < 12 and len(content) > 15:
            responsibilities.append(content)

        for sent in _split_sentences(content):
            sentences.append(sent)
            if section == "preferred":
                preferred_sentences.add(sent)
            names = find_skills(sent)
            if not names:
                continue
            preferred = section == "preferred" or bool(PREFERRED_CUES.search(sent))
            importance = "preferred" if preferred else "required"
            for n in names:
                existing = skills.get(n)
                if existing is None:
                    skills[n] = SkillRequirement(name=n, category=CATEGORY[n],
                                                 importance=importance, evidence=sent[:240])
                elif existing.importance == "preferred" and importance == "required":
                    existing.importance, existing.evidence = "required", sent[:240]

    skill_list = sorted(skills.values(), key=lambda s: (s.importance != "required", s.category, s.name))
    summary = " ".join(intro_lines[:2])[:320] or (lines[1][:320] if len(lines) > 1 else "")

    return ParsedJD(
        title=title,
        summary=summary,
        skills=skill_list,
        experience=extract_experience(sentences, title),
        education=extract_education(sentences, preferred_sentences),
        certifications=extract_certifications(text),
        responsibilities=responsibilities,
        soft_skills=extract_soft_skills(text),
        word_count=len(text.split()),
    )
