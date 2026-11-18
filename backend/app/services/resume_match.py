from typing import Any, Dict, Iterable, List, Sequence

from ..schemas import CandidateProfile, ParsedJD
from .semantic_match import semantic_similarity


def _normalize_name(value: str) -> str:
    return str(value).strip().lower()


def _skill_set(items: Iterable[str]) -> set:
    return {_normalize_name(item) for item in items if item and str(item).strip()}


def _coerce_jd(jd: Any) -> ParsedJD:
    if isinstance(jd, ParsedJD):
        return jd
    if isinstance(jd, dict):
        return ParsedJD(**jd)
    raise TypeError("Job description must be a ParsedJD instance or a dictionary.")


def _coerce_candidate(candidate: Any) -> CandidateProfile:
    if isinstance(candidate, CandidateProfile):
        return candidate
    if isinstance(candidate, dict):
        return CandidateProfile(**candidate)
    raise TypeError("Candidate must be a CandidateProfile instance or a dictionary.")


def score_resume_against_jd(jd: Any, candidate: Any) -> Dict[str, Any]:
    jd_obj = _coerce_jd(jd)
    candidate_obj = _coerce_candidate(candidate)

    jd_required = {s.name for s in jd_obj.skills if s.importance == "required"}
    jd_preferred = {s.name for s in jd_obj.skills if s.importance == "preferred"}
    candidate_skills = _skill_set(candidate_obj.skills or [])

    matched_required = sorted({s for s in jd_required if _normalize_name(s) in candidate_skills})
    matched_preferred = sorted({s for s in jd_preferred if _normalize_name(s) in candidate_skills})
    missing_required = sorted({s for s in jd_required if _normalize_name(s) not in candidate_skills})
    missing_preferred = sorted({s for s in jd_preferred if _normalize_name(s) not in candidate_skills})

    matched_skills = sorted(set(matched_required) | set(matched_preferred))
    missing_skills = sorted(set(missing_required) | set(missing_preferred))

    total_required = len(jd_required)
    total_preferred = len(jd_preferred)
    if total_required or total_preferred:
        req_ratio = len(matched_required) / total_required if total_required else 1.0
        pref_ratio = len(matched_preferred) / total_preferred if total_preferred else 1.0
        skill_component = min(1.0, (req_ratio * 0.7) + (pref_ratio * 0.3))
    else:
        skill_component = 1.0

    jd_text = " ".join([jd_obj.summary or "", *[s.evidence for s in jd_obj.skills]])
    candidate_text = " ".join([candidate_obj.summary or "", *candidate_obj.skills])
    semantic = semantic_similarity(jd_text, candidate_text)

    required_exp = jd_obj.experience.min_years
    candidate_exp = candidate_obj.experience_years
    if required_exp is None:
        experience_score = 1.0
    elif candidate_exp is None:
        experience_score = 0.0
    else:
        experience_score = min(candidate_exp / max(required_exp, 1.0), 1.0)

    if candidate_exp is None:
        candidate_exp = 0.0

    jd_fields = []
    for edu in jd_obj.education:
        jd_fields.extend(edu.fields)
    jd_fields_norm = _skill_set(jd_fields)
    candidate_edu_text = " ".join(candidate_obj.education or [])
    if not jd_fields_norm:
        education_score = 1.0
    else:
        education_score = 1.0 if any(_normalize_name(field) in _normalize_name(candidate_edu_text) for field in jd_fields_norm) else 0.35

    overall_score = (
        skill_component * 0.45
        + semantic * 0.25
        + experience_score * 0.20
        + education_score * 0.10
    ) * 100.0

    reasons = []
    if matched_required:
        reasons.append(f"Matches the core required skills: {', '.join(matched_required)}.")
    if missing_required:
        reasons.append(f"Missing required skills: {', '.join(missing_required)}.")
    if matched_preferred:
        reasons.append(f"Includes preferred skills: {', '.join(matched_preferred)}.")
    if semantic >= 0.7:
        reasons.append("Strong semantic similarity between the JD and the candidate profile.")
    elif semantic >= 0.45:
        reasons.append("Moderate semantic similarity indicates a good conceptual match.")
    else:
        reasons.append("Semantic similarity is weak; the candidate text aligns less closely with the JD.")
    if required_exp is None:
        reasons.append("No minimum experience requirement was specified in the JD.")
    elif candidate_exp is not None:
        if candidate_exp >= required_exp:
            reasons.append(f"Experience meets the requirement: {candidate_exp} years vs {required_exp} years required.")
        else:
            reasons.append(f"Experience is below the requirement: {candidate_exp} years vs {required_exp} years required.")
    if jd_fields_norm and candidate_edu_text:
        if education_score >= 0.9:
            reasons.append("Education aligns with the role requirements.")
        else:
            reasons.append("Education only partly aligns with the target role.")

    return {
        "overall_score": round(float(overall_score), 2),
        "semantic_similarity": round(float(semantic), 4),
        "skill_match_score": round(float(skill_component * 100), 2),
        "experience_match_score": round(float(experience_score), 4),
        "education_match_score": round(float(education_score), 4),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "matched_required_skills": matched_required,
        "missing_required_skills": missing_required,
        "matched_preferred_skills": matched_preferred,
        "missing_preferred_skills": missing_preferred,
        "candidate_experience_years": candidate_exp,
        "required_experience_years": required_exp,
        "relevant_experience": candidate_exp is not None and required_exp is not None and candidate_exp >= required_exp,
        "experience_comparison": f"{candidate_exp} years vs {required_exp} years required" if candidate_exp is not None and required_exp is not None else "Experience requirement not specified",
        "reasons": reasons,
    }
