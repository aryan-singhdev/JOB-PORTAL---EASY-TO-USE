# JobMatch — Resume-Based Job Recommendation Portal

A full-stack Python web app (Flask) where a user signs up, logs in, uploads
their resume, and instantly sees job openings — aggregated from multiple
platforms (LinkedIn, Indeed, Naukri, Glassdoor, Monster) — ranked by how well
each job matches the skills detected in their resume.

## Features

- **Login / Signup** — session-based authentication with hashed passwords (Werkzeug).
- **Resume upload** — accepts PDF, DOCX, or TXT resumes.
- **Automatic skill extraction** — parses resume text and detects ~100 common
  tech/business skills (Python, React, AWS, SQL, Data Science, Digital
  Marketing, etc.). You can also manually add/remove skills.
- **Multi-platform job aggregation** — a dataset of jobs tagged by source
  platform (LinkedIn, Indeed, Naukri, Glassdoor, Monster). In production you'd
  replace `data/jobs.json` with live calls to each platform's job-search API
  (or a scraping/ETL pipeline) that normalizes results into the same schema.
- **Smart matching** — each job gets a match percentage based on the overlap
  between the job's required skills and your skill profile, with matched vs.
  missing skills highlighted.
- **Platform filter** — narrow matched jobs down to a specific platform.

## Project Structure

```
job_portal/
├── app.py                  # Flask app & routes
├── db.py                   # SQLite data layer (users table)
├── requirements.txt
├── utils/
│   ├── resume_parser.py    # PDF/DOCX text extraction + skill detection
│   └── job_matcher.py      # Job ranking / matching engine
├── data/
│   ├── jobs.json           # Mock aggregated job listings (multiple platforms)
│   └── skills_master.json  # Master skills vocabulary used for matching
├── templates/              # Jinja2 HTML templates (Bootstrap 5 styling)
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── jobs.html
├── static/css/style.css
└── uploads/                # Uploaded resumes are stored here (gitignore this)
```

## Setup

```bash
cd job_portal
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

The SQLite database (`job_portal.db`) is created automatically on first run.

## How it works

1. **Sign up / Log in** → session cookie stores your `user_id`.
2. **Dashboard** → upload a resume file. `utils/resume_parser.py` extracts
   raw text (via `pdfplumber` for PDFs, `python-docx` for Word docs) and scans
   it against `data/skills_master.json` using word-boundary regex matching.
   Detected skills are saved to your profile; you can add/remove skills
   manually from the checklist.
3. **Matched Jobs** → `utils/job_matcher.py` loads `data/jobs.json` (jobs
   labeled by their source platform) and computes, for every job, the percent
   of required skills you already have. Jobs are sorted best-match first, and
   you can filter by platform.

## Going further (ideas)

- Swap `data/jobs.json` for real integrations: LinkedIn Jobs API, Indeed
  Publisher API, Naukri/Glassdoor scraping via a scheduled ETL job that
  writes into the same `jobs` schema (id, title, company, location, platform,
  url, skills, description).
- Move skill extraction to an NLP model (spaCy NER / an LLM) for more
  accurate, non-keyword-based skill inference.
- Add pagination, saved/bookmarked jobs, and email alerts for new matches.
- Replace SQLite with PostgreSQL and add Flask-Migrate for schema changes.
- Add resume "strength" scoring/feedback tips per job (which skills to learn
  next to raise your match score).
