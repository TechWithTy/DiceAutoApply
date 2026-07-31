from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List

from pypdf import PdfReader

from _data_.Profiles.main_profile import user_profile
from _data_.Resumes.indeedResumes import get_indeed_resume_config
from backend.resume_builder.generator import generate_resume


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
SOURCE_PROFILE_DIR = Path(__file__).resolve().parent / "data" / "source_profiles"
GENERATED_PROFILE_DIR = Path(__file__).resolve().parent / "data" / "generated_profiles"
STOPWORDS = {
    "about", "after", "also", "an", "and", "are", "as", "at", "be", "been", "build", "building",
    "by", "for", "from", "have", "in", "into", "is", "it", "of", "on", "or", "that", "the",
    "their", "this", "to", "using", "with", "you", "your",
}
SECTION_BREAKERS = {
    "contact",
    "expertise",
    "phone",
    "email",
    "location",
    "experience",
    "education",
    "certifications",
    "book appointment here",
}


def resolve_repo_path(raw_path: str) -> Path | None:
    if not raw_path:
        return None

    path = Path(raw_path)
    candidates = [path]
    if not path.is_absolute():
        candidates.extend([REPO_ROOT / path, Path.cwd() / path])

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return None


def _normalized_resume_key(raw_path: str) -> str:
    resolved = resolve_repo_path(raw_path)
    if resolved:
        try:
            return resolved.relative_to(REPO_ROOT).as_posix().casefold()
        except Exception:
            return resolved.as_posix().casefold()
    return raw_path.replace("\\", "/").casefold()


def _load_source_profile_index() -> list[dict[str, Any]]:
    roots = [SOURCE_PROFILE_DIR, GENERATED_PROFILE_DIR]
    profiles: list[dict[str, Any]] = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.glob("*.json")):
            try:
                profiles.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
    return profiles


def load_structured_resume_profile(resume_path: str) -> dict[str, Any] | None:
    wanted = _normalized_resume_key(resume_path)
    for profile in _load_source_profile_index():
        for candidate in profile.get("resume_paths", []):
            if _normalized_resume_key(candidate) == wanted:
                return profile
    return None


def _profile_resume_sources(profile=user_profile) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for job_title in getattr(profile, "job_titles", []):
        items.append(
            {
                "label": f"{job_title.title} Resume",
                "path": getattr(job_title, "relevant_resume_path", ""),
                "job_titles": [job_title.title],
                "source": "profile",
            }
        )
    return items


def _indeed_resume_sources() -> list[dict[str, Any]]:
    config = get_indeed_resume_config()
    items: list[dict[str, Any]] = []
    for resume in config.get("resumes", []):
        items.append(
            {
                "label": resume.get("label", "Indeed Resume"),
                "path": resume.get("path", ""),
                "job_titles": resume.get("job_titles", []),
                "source": "indeed",
            }
        )
    return items


def collect_resume_sources(profile=user_profile) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for source in [*_profile_resume_sources(profile), *_indeed_resume_sources()]:
        resolved = resolve_repo_path(source.get("path", ""))
        key = str(resolved or source.get("path", ""))
        if not key:
            continue
        merged = deduped.setdefault(
            key,
            {
                "label": source["label"],
                "path": str(resolved or source["path"]),
                "job_titles": [],
                "source": source["source"],
                "exists": bool(resolved),
            },
        )
        merged["job_titles"] = sorted(set([*merged["job_titles"], *source.get("job_titles", [])]))
        merged["structured_profile"] = bool(load_structured_resume_profile(merged["path"]))
    return sorted(deduped.values(), key=lambda item: (not item["exists"], item["label"].lower()))


def extract_resume_text(resume_path: str) -> str:
    resolved = resolve_repo_path(resume_path)
    if not resolved:
        return ""

    suffix = resolved.suffix.lower()
    try:
        if suffix in {".txt", ".md"}:
            return resolved.read_text(encoding="utf-8", errors="ignore")
        if suffix == ".pdf":
            return "\n".join((page.extract_text() or "") for page in PdfReader(str(resolved)).pages)
    except Exception:
        return ""
    return ""


def _clean_lines(text: str) -> list[str]:
    return [line.strip(" -|\t") for line in text.splitlines() if line and line.strip(" -|\t")]


def _section_bounds(lines: list[str], section_name: str) -> tuple[int | None, int | None]:
    start = None
    for index, line in enumerate(lines):
        if line.casefold() == section_name.casefold():
            start = index + 1
            break
    if start is None:
        return None, None

    end = len(lines)
    for index in range(start, len(lines)):
        lowered = lines[index].casefold()
        if index > start and lowered in {"experience", "education", "certifications"}:
            end = index
            break
    return start, end


def _section_lines(text: str, section_name: str) -> list[str]:
    lines = _clean_lines(text)
    start, end = _section_bounds(lines, section_name)
    if start is None:
        return []
    return lines[start:end]


def _extract_focus_keywords(job_description: str, existing_skills: Iterable[str], limit: int = 8) -> list[str]:
    existing = {skill.casefold() for skill in existing_skills}
    words = re.findall(r"[A-Za-z][A-Za-z0-9.+#/-]{2,}", job_description or "")
    counts = Counter(word for word in words if word.casefold() not in STOPWORDS)
    ordered = [word for word, _ in counts.most_common() if word.casefold() not in existing]
    result: list[str] = []
    for word in ordered:
        if word not in result:
            result.append(word)
        if len(result) >= limit:
            break
    return result


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _merge_wrapped_lines(lines: list[str]) -> list[str]:
    merged: list[str] = []
    for line in lines:
        line = _normalize_space(line)
        if not line:
            continue
        if merged and (
            (not re.search(r"[.!?:]$", merged[-1]) and line[:1].islower())
            or re.match(r"^\d+[%)]?\s", line)
        ):
            merged[-1] = f"{merged[-1]} {line}"
        else:
            merged.append(line)
    return merged


def _is_role_header(line: str) -> bool:
    return bool(
        re.search(r"(?:\d{1,2}/\d{4}|\d{4})\s*[-–]\s*(?:Present|\d{1,2}/\d{4}|\d{4})", line, re.IGNORECASE)
        and "|" in line
    )


def _split_role_header(line: str) -> dict[str, str]:
    match = re.search(
        r"(?P<dates>(?:\d{1,2}/\d{4}|\d{4})\s*[-–]\s*(?:Present|\d{1,2}/\d{4}|\d{4}))",
        line,
        re.IGNORECASE,
    )
    dates = match.group("dates").strip() if match else ""
    header = line[: match.start()].strip(" |-") if match else line.strip(" |-")
    parts = [part.strip() for part in header.split("|") if part.strip()]

    title = parts[0] if parts else header
    org = ""
    if len(parts) >= 2:
        org = parts[-1]
        middle = [part for part in parts[1:-1] if part]
        if middle:
            title = f"{title} | {' | '.join(middle)}"
    return {"title": title, "org": org, "dates": dates}


def _candidate_bullets(lines: list[str]) -> list[str]:
    return [
        line
        for line in lines
        if len(line) > 35
        and line.casefold() not in SECTION_BREAKERS
        and line != "Data is the compass guiding us through the complexities of life"
        and not re.fullmatch(r"[A-Z][A-Za-z &/]+", line)
        and not re.search(r"\d{4}", line)
        and not _is_role_header(line)
    ]


def _parse_experience(text: str) -> list[dict[str, Any]]:
    lines = _merge_wrapped_lines(_section_lines(text, "Experience"))
    if not lines or not any(_is_role_header(line) for line in lines):
        lines = _merge_wrapped_lines(_clean_lines(text))

    header_indexes = [index for index, line in enumerate(lines) if _is_role_header(line)]
    if header_indexes:
        roles: list[dict[str, Any]] = []
        previous_header_index = -1
        for position, header_index in enumerate(header_indexes):
            header = _split_role_header(lines[header_index])
            chunk_before = lines[previous_header_index + 1:header_index]
            bullets_before = _candidate_bullets(chunk_before)
            next_header_index = header_indexes[position + 1] if position + 1 < len(header_indexes) else len(lines)
            chunk_after = lines[header_index + 1:next_header_index]
            bullets_after = _candidate_bullets(chunk_after)
            bullets = bullets_before[-4:] if bullets_before else bullets_after[:4]
            roles.append(
                {
                    "org": header["org"],
                    "title": header["title"],
                    "dates": header["dates"],
                    "location": "Remote",
                    "bullets": bullets,
                }
            )
            previous_header_index = header_index
        return roles[:4]

    roles: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in lines:
        if _is_role_header(line):
            if current:
                current["bullets"] = current["bullets"][:4]
                roles.append(current)
            header = _split_role_header(line)
            current = {
                "org": header["org"],
                "title": header["title"],
                "dates": header["dates"],
                "location": "Remote",
                "bullets": [],
            }
            continue

        lowered = line.casefold()
        if lowered in SECTION_BREAKERS or line == "Data is the compass guiding us through the complexities of life":
            continue

        if current and len(line) > 35 and not re.fullmatch(r"[A-Z][A-Za-z &/]+", line):
            current["bullets"].append(line)

    if current:
        current["bullets"] = current["bullets"][:4]
        roles.append(current)
    return roles[:4]


def _parse_education(text: str) -> list[dict[str, str]]:
    lines = _merge_wrapped_lines(_clean_lines(text))
    education: list[dict[str, str]] = []
    for index, line in enumerate(lines):
        lowered = line.casefold()
        if "university" not in lowered and "college" not in lowered:
            continue

        school_parts = [line]
        used_previous_school_part = False
        used_next_school_part = False
        if lowered in {"university", "college"} and index > 0:
            school_parts.insert(0, lines[index - 1])
            used_previous_school_part = True
        elif index + 1 < len(lines):
            next_line = lines[index + 1]
            if next_line.casefold() in {"university", "college"}:
                school_parts.append(next_line)
                used_next_school_part = True

        degree_parts: list[str] = []
        back = index - 1
        if lowered in {"university", "college"}:
            back = index - 2
        while back >= 0:
            candidate = lines[back]
            if candidate.casefold() in SECTION_BREAKERS or _is_role_header(candidate) or re.search(r"\d{4}", candidate):
                break
            if len(candidate) <= 40 and candidate != "Data is the compass guiding us through the complexities of life":
                degree_parts.insert(0, candidate)
                back -= 1
                continue
            break

        dates = ""
        forward = index + 1
        if used_next_school_part:
            forward = index + 2
        if forward < len(lines) and re.search(r"\d{4}", lines[forward]):
            dates = lines[forward]
        elif forward + 1 < len(lines) and re.search(r"\d{4}", lines[forward + 1]):
            dates = lines[forward + 1]

        education.append(
            {
                "school": _normalize_space(" ".join(school_parts)),
                "degree": _normalize_space(" ".join(degree_parts[-2:])),
                "dates": dates,
            }
        )

    unique: list[dict[str, str]] = []
    seen = set()
    for item in education:
        key = (item["school"], item["degree"], item["dates"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique[:3]


def _parse_certifications(text: str) -> list[str]:
    lines = _merge_wrapped_lines(_clean_lines(text))
    results: list[str] = []
    buffer = ""
    for index, line in enumerate(lines):
        lowered = line.casefold()
        if lowered in SECTION_BREAKERS:
            continue
        if "university" in lowered or "college" in lowered:
            if buffer:
                results.append(_normalize_space(buffer))
                buffer = ""
            continue
        if line in {"CASP", "CISSP"}:
            if buffer:
                results.append(_normalize_space(buffer))
                buffer = ""
            if line not in results:
                results.append(line)
            continue
        if buffer and (
            lowered.endswith("certificate")
            or lowered.endswith("certification")
            or lowered.endswith("associate")
            or lowered == "professional certificate"
            or lowered == "engineer associate"
        ):
            buffer = f"{buffer} {line}"
            continue
        if lowered in {"professional certificate", "engineer associate"} and index > 0:
            previous = lines[index - 1]
            previous_lowered = previous.casefold()
            if previous_lowered not in SECTION_BREAKERS and not _is_role_header(previous) and not re.search(r"\d{4}", previous):
                buffer = f"{previous} {line}"
                continue
        if "cert" in lowered or "professional" in lowered or lowered.startswith("microsoft certified"):
            if buffer:
                results.append(_normalize_space(buffer))
            buffer = line
            continue
        if buffer:
            if len(line) <= 40 and not _is_role_header(line) and not re.search(r"\d{4}", line):
                buffer = f"{buffer} {line}"
            else:
                results.append(_normalize_space(buffer))
                buffer = ""
    if buffer:
        results.append(_normalize_space(buffer))
    deduped: list[str] = []
    for line in results:
        if line not in deduped:
            deduped.append(line)
    return deduped[:6]


def _make_links_line(profile) -> str:
    parts: list[str] = []
    online_presence = getattr(profile, "online_presence", {}) or {}
    if online_presence.get("portfolio"):
        parts.append(f"Portfolio: {online_presence['portfolio']}")
    if online_presence.get("website"):
        parts.append(f"Website: {online_presence['website']}")
    if getattr(profile, "linkedin_profile", ""):
        parts.append(f"LinkedIn: {profile.linkedin_profile}")
    return " • ".join(parts)


def _merge_skill_sections(
    structured_sections: list[dict[str, Any]],
    base_skills: list[str],
    focus_keywords: list[str],
    extra_skills: list[str],
) -> list[dict[str, Any]]:
    sections = [section for section in structured_sections if section.get("items")]
    if base_skills:
        sections.append({"label": "Target Role", "items": base_skills[:10]})
    if focus_keywords:
        sections.append({"label": "Focus Keywords", "items": focus_keywords[:8]})
    if extra_skills:
        sections.append({"label": "Additional", "items": extra_skills[:8]})
    return sections


def _fallback_experience(profile, target_job_title: str, focus_keywords: list[str]) -> list[dict[str, Any]]:
    bullets = [
        f"Targeting {target_job_title} roles with emphasis on {', '.join(focus_keywords[:4]) or 'core engineering delivery'}.",
        f"Brings experience across {', '.join(getattr(profile.job_titles[0], 'skills', [])[:5])}.",
    ]
    return [
        {
            "org": "Profile-Based Experience Summary",
            "title": target_job_title,
            "dates": "Current",
            "location": f"{getattr(profile, 'city', '')}, {getattr(profile, 'country', '')}".strip(", "),
            "bullets": bullets,
        }
    ]


def build_optimized_resume_payload(
    *,
    target_job_title: str,
    source_resume_paths: list[str],
    target_company: str = "",
    target_role: str = "",
    job_description: str = "",
    custom_summary: str = "",
    additional_skills: str = "",
    profile=user_profile,
) -> dict[str, Any]:
    target = next((job for job in getattr(profile, "job_titles", []) if job.title == target_job_title), None)
    target = target or getattr(profile, "job_titles", [None])[0]
    role_title = (target_role or target_job_title or getattr(target, "title", "Software Engineer")).strip()

    resume_texts = [extract_resume_text(path) for path in source_resume_paths]
    combined_text = "\n".join(text for text in resume_texts if text.strip())
    structured_profiles = [item for item in (load_structured_resume_profile(path) for path in source_resume_paths) if item]

    base_skills = list(getattr(target, "skills", [])) if target else []
    extra_skills = [skill.strip() for skill in additional_skills.split(",") if skill.strip()]
    focus_keywords = _extract_focus_keywords(job_description, [*base_skills, *extra_skills])

    summary_parts = []
    if custom_summary.strip():
        summary_parts.append(custom_summary.strip())
    elif structured_profiles and structured_profiles[0].get("summary"):
        summary_parts.append(structured_profiles[0]["summary"].strip())
    elif getattr(profile, "about_me", "").strip():
        summary_parts.append(getattr(profile, "about_me").strip())
    summary_parts.append(f"Targeting {role_title} roles" + (f" at {target_company.strip()}" if target_company.strip() else "") + ".")
    if focus_keywords:
        summary_parts.append(f"Optimized around {', '.join(focus_keywords[:6])}.")

    structured_experience = [entry for profile_data in structured_profiles for entry in profile_data.get("experience", [])]
    structured_education = [entry for profile_data in structured_profiles for entry in profile_data.get("education", [])]
    structured_certifications = [entry for profile_data in structured_profiles for entry in profile_data.get("certifications", [])]
    structured_skills = [entry for profile_data in structured_profiles for entry in profile_data.get("skills", [])]

    experience = structured_experience or _parse_experience(combined_text)
    if not experience:
        experience = _fallback_experience(profile, role_title, focus_keywords)

    contact = [
        ", ".join(part for part in [getattr(profile, "city", ""), getattr(profile, "country", "")] if part),
        getattr(profile, "phone_number", ""),
        getattr(profile, "email", ""),
    ]
    contact = [part for part in contact if part]

    payload = {
        "name": getattr(profile, "name", "").strip() or "Candidate",
        "headline": role_title,
        "contact": contact,
        "links_line": _make_links_line(profile),
        "summary": " ".join(part for part in summary_parts if part),
        "skills": _merge_skill_sections(structured_skills, base_skills, focus_keywords, extra_skills),
        "experience": experience,
        "education": structured_education or _parse_education(combined_text),
        "certifications": structured_certifications or _parse_certifications(combined_text),
        "source_resume_paths": source_resume_paths,
        "structured_source_ids": [profile_data.get("id", "") for profile_data in structured_profiles if profile_data.get("id")],
        "source_resume_excerpt": combined_text[:2000],
    }
    payload["skills"] = [section for section in payload["skills"] if section.get("items")]
    return payload


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug or "resume"


def _sanitize_generated_profile_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "headline": payload.get("headline", ""),
        "summary": payload.get("summary", ""),
        "skills": payload.get("skills", []),
        "experience": payload.get("experience", []),
        "education": payload.get("education", []),
        "certifications": payload.get("certifications", []),
    }


def save_generated_resume_profile(
    *,
    payload: dict[str, Any],
    output_pdf_path: str,
    profile_name: str,
    target_job_title: str,
    target_company: str = "",
) -> Path:
    GENERATED_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    profile_id = f"generated_{_slugify(profile_name)}"
    file_path = GENERATED_PROFILE_DIR / f"{profile_id}.json"
    stored = {
        "id": profile_id,
        "resume_paths": [output_pdf_path],
        "headline": payload.get("headline", target_job_title),
        "summary": payload.get("summary", ""),
        "skills": payload.get("skills", []),
        "experience": payload.get("experience", []),
        "education": payload.get("education", []),
        "certifications": payload.get("certifications", []),
        "metadata": {
            "generated_on": "2026-07-21",
            "profile_name": profile_name,
            "target_job_title": target_job_title,
            "target_company": target_company,
            "source_resume_paths": payload.get("source_resume_paths", []),
            "structured_source_ids": payload.get("structured_source_ids", []),
        },
    }
    file_path.write_text(json.dumps(stored, indent=2), encoding="utf-8")
    return file_path


def generate_optimized_resume(
    *,
    payload: dict[str, Any],
    output_name: str,
    template_id: str = "standard",
) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = _slugify(output_name)
    if not filename.endswith(".pdf"):
        filename = f"{filename}.pdf"
    out_path = OUTPUT_DIR / filename
    generate_resume(template_id, payload, str(out_path))
    return out_path
