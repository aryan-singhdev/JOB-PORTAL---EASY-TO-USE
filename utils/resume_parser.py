"""
Resume parsing utilities.
Extracts raw text from an uploaded PDF or DOCX resume, then matches that
text against a master list of known skills to build a candidate skill profile.
"""
import os
import json
import re

_SKILLS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "skills_master.json"
)

with open(_SKILLS_PATH, "r", encoding="utf-8") as f:
    MASTER_SKILLS = json.load(f)


def extract_text_from_pdf(filepath):
    import pdfplumber
    text = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n".join(text)


def extract_text_from_docx(filepath):
    import docx
    document = docx.Document(filepath)
    return "\n".join(p.text for p in document.paragraphs)


def extract_text_from_txt(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_text(filepath):
    ext = filepath.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        return extract_text_from_pdf(filepath)
    elif ext == "docx":
        return extract_text_from_docx(filepath)
    elif ext == "txt":
        return extract_text_from_txt(filepath)
    else:
        raise ValueError(f"Unsupported resume file type: .{ext}")


def extract_skills(text, skill_list=None):
    """
    Match known skills inside the resume text.
    Uses word-boundary based matching so 'go' doesn't match inside 'google', etc.
    Returns a sorted list of matched skills (lowercase, as they appear in the master list).
    """
    if skill_list is None:
        skill_list = MASTER_SKILLS

    text_lower = text.lower()
    found = set()
    for skill in skill_list:
        skill_lower = skill.lower()
        # Build a tolerant regex: escape special chars (skills contain '.', '+', '#', '/')
        pattern = r"(?<![a-z0-9])" + re.escape(skill_lower) + r"(?![a-z0-9])"
        if re.search(pattern, text_lower):
            found.add(skill_lower)
    return sorted(found)


def parse_resume(filepath):
    """
    Full pipeline: extract text from the resume file and return (raw_text, skills_found).
    """
    text = extract_text(filepath)
    skills = extract_skills(text)
    return text, skills
