"""
Job matching engine.
Loads the aggregated job dataset (simulating jobs pulled in from multiple
platforms such as LinkedIn, Indeed, Naukri, Glassdoor, Monster) and ranks
jobs against a candidate's skill set.
"""
import os
import json

_JOBS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "jobs.json"
)


def load_jobs():
    with open(_JOBS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_platforms(jobs=None):
    jobs = jobs or load_jobs()
    return sorted({job["platform"] for job in jobs})


def match_score(user_skills, job_skills):
    """
    Returns (match_percent, matched_skills, missing_skills).
    match_percent is based on how many of the job's required skills the
    candidate already has (0-100).
    """
    user_set = {s.lower().strip() for s in user_skills if s.strip()}
    job_set = {s.lower().strip() for s in job_skills}

    if not job_set:
        return 0, [], []

    matched = sorted(user_set & job_set)
    missing = sorted(job_set - user_set)
    percent = round(len(matched) / len(job_set) * 100)
    return percent, matched, missing


def match_jobs(user_skills, jobs=None, min_score=1, platform=None):
    """
    Rank every job in the dataset for the given user skills.
    Only jobs with match_percent >= min_score are returned, sorted best first.
    """
    jobs = jobs or load_jobs()
    results = []

    for job in jobs:
        if platform and job["platform"] != platform:
            continue
        percent, matched, missing = match_score(user_skills, job["skills"])
        if percent >= min_score:
            enriched = dict(job)
            enriched["match_percent"] = percent
            enriched["matched_skills"] = matched
            enriched["missing_skills"] = missing
            results.append(enriched)

    results.sort(key=lambda j: j["match_percent"], reverse=True)
    return results
