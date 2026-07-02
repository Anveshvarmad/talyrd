import json
import re
from openai import OpenAI
from app.config import OPENAI_API_KEY, OPENAI_MODEL

SECTION_HEADERS = {
    "summary": ["summary", "professional summary", "profile"],
    "skills": ["skills", "technical skills", "technologies"],
    "experience": ["experience", "work experience", "professional experience"],
    "projects": ["projects", "project experience"],
    "education": ["education", "academic background"]
}

def tailor_resume_with_openai(
    full_name,
    target_role,
    resume_text,
    job_description,
    ats_analysis
):
    fallback = parse_resume_sections(resume_text)

    if OPENAI_API_KEY:
        try:
            data = call_openai(full_name, target_role, resume_text, job_description, ats_analysis, fallback)
        except Exception as error:
            print("OPENAI_TAILOR_ERROR", str(error))
            data = build_fallback_data(full_name, target_role, fallback)
    else:
        data = build_fallback_data(full_name, target_role, fallback)

    data = normalize_resume_data(data, fallback, ats_analysis)
    data = enforce_one_page_resume(data)
    data = inject_missing_keywords(data, ats_analysis)

    plain_text = compose_resume_text(data)

    cover_letter = data.get("cover_letter_text") or build_cover_letter(full_name, target_role, data)
    improvement_summary = data.get("improvement_summary") or (
        "Generated a one-page ATS-optimized resume with structured sections, concise bullets, "
        "role-specific keywords, and professional formatting."
    )

    return {
        "resume_sections": flatten_for_existing_routes(data),
        "resume_data": data,
        "tailored_resume_text": plain_text,
        "cover_letter_text": cover_letter,
        "improvement_summary": improvement_summary
    }

def call_openai(full_name, target_role, resume_text, job_description, ats_analysis, fallback):
    client = OpenAI(api_key=OPENAI_API_KEY)

    instructions = """
You are Talyrd, a professional resume optimization engine.

Generate a REAL one-page resume, not plain keyword text.

The resume must include:
1. Professional Summary
2. Technical Skills
3. Professional Experience
4. Projects
5. Education

Formatting expectations:
- Experience must preserve company, title, location, dates, and detailed achievement bullets.
- Projects must preserve project name, tech stack, and achievement bullets.
- Education must include school, degree, location, dates, and coursework if available.
- Use strong one-line bullets.
- Make it detailed but compact enough for one page.
- Optimize for ATS keywords from the job description.
- Add missing job keywords naturally into skills or bullets when possible.
- Do not invent fake employers, schools, dates, degrees, or certifications.
- Do not return empty sections.
- Return JSON only.

Return exactly this JSON:
{
  "summary": "2 sentence professional summary",
  "skills": {
    "languages": ["Python"],
    "backend": ["FastAPI"],
    "frontend": ["React"],
    "databases": ["PostgreSQL"],
    "cloud_devops": ["AWS"],
    "ai_tools": ["OpenAI APIs"],
    "practices": ["Agile"]
  },
  "experience": [
    {
      "company": "Company Name",
      "title": "Job Title",
      "location": "City, State",
      "dates": "MMM YYYY - MMM YYYY",
      "bullets": ["achievement bullet"]
    }
  ],
  "projects": [
    {
      "name": "Project Name",
      "tech_stack": "Python, Flask, PostgreSQL",
      "bullets": ["achievement bullet"]
    }
  ],
  "education": [
    {
      "school": "University Name",
      "degree": "Degree Name",
      "location": "City, State",
      "dates": "MMM YYYY - MMM YYYY",
      "details": ["coursework or note"]
    }
  ],
  "cover_letter_text": "short professional cover letter",
  "improvement_summary": "short explanation"
}
"""

    payload = {
        "full_name": full_name,
        "target_role": target_role,
        "original_resume": resume_text,
        "job_description": job_description,
        "ats_analysis": ats_analysis,
        "fallback_resume_sections": fallback,
        "one_page_rules": {
            "summary_sentences": 2,
            "experience_entries_max": 3,
            "bullets_per_experience_max": 2,
            "projects_max": 2,
            "bullets_per_project_max": 1,
            "education_entries_max": 1,
            "bullet_words_max": 22
        }
    }

    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=instructions,
        input=json.dumps(payload),
        temperature=0.15,
        max_output_tokens=3500
    )

    raw = response.output_text.strip()
    print("OPENAI_RAW_OUTPUT_START")
    print(raw[:3000])
    print("OPENAI_RAW_OUTPUT_END")

    return parse_json(raw)

def parse_json(text):
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise ValueError("OpenAI response was not valid JSON")
        return json.loads(match.group(0))

def parse_resume_sections(resume_text):
    sections = {
        "summary": "",
        "skills": [],
        "experience": [],
        "projects": [],
        "education": []
    }

    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    current = "summary"

    header_lookup = {}

    for section, headers in SECTION_HEADERS.items():
        for header in headers:
            header_lookup[header] = section

    for line in lines:
        normalized = line.lower().strip(":").strip()

        if normalized in header_lookup:
            current = header_lookup[normalized]
            continue

        clean_line = line.lstrip("-•* ").strip()

        if current == "summary":
            sections["summary"] = (sections["summary"] + " " + clean_line).strip()
        elif current == "skills":
            if "," in clean_line:
                sections["skills"].extend([item.strip() for item in clean_line.split(",") if item.strip()])
            else:
                sections["skills"].append(clean_line)
        elif current == "experience":
            sections["experience"].append(clean_line)
        elif current == "projects":
            sections["projects"].append(clean_line)
        elif current == "education":
            sections["education"].append(clean_line)

    if not sections["summary"]:
        useful = [
            line for line in lines[:8]
            if "@" not in line and "linkedin" not in line.lower() and "github" not in line.lower()
        ]
        sections["summary"] = " ".join(useful[:3])

    return sections

def normalize_resume_data(data, fallback, ats_analysis):
    if not isinstance(data, dict):
        data = {}

    summary = clean_text(data.get("summary")) or fallback.get("summary") or (
        "Software Engineer experienced in backend systems, full-stack development, REST APIs, and cloud-based software delivery."
    )

    skills = normalize_skills(data.get("skills"), fallback.get("skills", []), ats_analysis.get("job_keywords", []))
    experience = normalize_experience(data.get("experience"), fallback.get("experience", []))
    projects = normalize_projects(data.get("projects"), fallback.get("projects", []))
    education = normalize_education(data.get("education"), fallback.get("education", []))

    return {
        "summary": summary,
        "skills": skills,
        "experience": experience,
        "projects": projects,
        "education": education,
        "cover_letter_text": clean_text(data.get("cover_letter_text")),
        "improvement_summary": clean_text(data.get("improvement_summary"))
    }

def normalize_skills(value, fallback_skills, job_keywords):
    categories = {
        "languages": [],
        "backend": [],
        "frontend": [],
        "databases": [],
        "cloud_devops": [],
        "ai_tools": [],
        "practices": []
    }

    if isinstance(value, dict):
        for key in categories:
            categories[key] = unique_list(value.get(key, []))

    elif isinstance(value, list):
        categories["languages"] = unique_list(value)

    elif isinstance(value, str):
        categories["languages"] = unique_list(value.split(","))

    fallback_items = unique_list(fallback_skills)
    keyword_items = unique_list(job_keywords)

    all_known = set()

    for items in categories.values():
        for item in items:
            all_known.add(item.lower())

    for item in fallback_items + keyword_items:
        lower = item.lower()

        if lower in all_known:
            continue

        if any(x in lower for x in ["python", "java", "javascript", "typescript", "c++", "sql"]):
            categories["languages"].append(item)
        elif any(x in lower for x in ["django", "flask", "fastapi", "node", "api", "microservice", "backend"]):
            categories["backend"].append(item)
        elif any(x in lower for x in ["react", "angular", "html", "css", "frontend"]):
            categories["frontend"].append(item)
        elif any(x in lower for x in ["postgres", "mysql", "mongo", "redis", "database", "sql"]):
            categories["databases"].append(item)
        elif any(x in lower for x in ["aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "jenkins", "deployment", "devops"]):
            categories["cloud_devops"].append(item)
        elif any(x in lower for x in ["openai", "llm", "rag", "embedding", "ai", "ml"]):
            categories["ai_tools"].append(item)
        else:
            categories["practices"].append(item)

        all_known.add(lower)

    for key in categories:
        categories[key] = unique_list(categories[key])[:9]

    return categories

def normalize_experience(value, fallback_lines):
    entries = []

    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                entries.append({
                    "company": clean_text(item.get("company")) or "Professional Experience",
                    "title": clean_text(item.get("title")) or "Software Engineer",
                    "location": clean_text(item.get("location")),
                    "dates": clean_text(item.get("dates")),
                    "bullets": unique_list(item.get("bullets", []))[:3]
                })

    if not entries:
        bullets = unique_list(fallback_lines)[:6]
        entries = [{
            "company": "Professional Experience",
            "title": "Software Engineer",
            "location": "",
            "dates": "",
            "bullets": bullets[:3] or [
                "Built backend services, REST APIs, and database-driven workflows for production software systems."
            ]
        }]

    return entries[:3]

def normalize_projects(value, fallback_lines):
    projects = []

    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                projects.append({
                    "name": clean_text(item.get("name")) or "Software Engineering Project",
                    "tech_stack": clean_text(item.get("tech_stack")),
                    "bullets": unique_list(item.get("bullets", []))[:2]
                })

    if not projects:
        bullets = unique_list(fallback_lines)[:4]
        projects = [{
            "name": "Software Engineering Project",
            "tech_stack": "Python, Flask, PostgreSQL, Docker",
            "bullets": bullets[:2] or [
                "Delivered backend functionality with APIs, database workflows, and deployment-ready architecture."
            ]
        }]

    return projects[:2]

def normalize_education(value, fallback_lines):
    education = []

    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                education.append({
                    "school": clean_text(item.get("school")) or "University",
                    "degree": clean_text(item.get("degree")),
                    "location": clean_text(item.get("location")),
                    "dates": clean_text(item.get("dates")),
                    "details": unique_list(item.get("details", []))[:1]
                })

    if not education:
        lines = unique_list(fallback_lines)
        education = [{
            "school": lines[0] if lines else "New York University",
            "degree": lines[1] if len(lines) > 1 else "Master of Science, Computer Engineering",
            "location": "",
            "dates": "",
            "details": lines[2:3]
        }]

    return education[:1]

def inject_missing_keywords(data, ats_analysis):
    resume_text = compose_resume_text(data).lower()
    missing = ats_analysis.get("missing_keywords", [])

    extra_keywords = []

    for keyword in missing:
        if keyword.lower() not in resume_text:
            extra_keywords.append(keyword)

    if extra_keywords:
        current = data["skills"].get("practices", [])
        data["skills"]["practices"] = unique_list(current + extra_keywords)[:12]

    return data

def enforce_one_page_resume(data):
    data["summary"] = limit_words(data["summary"], 42)

    for key in data["skills"]:
        data["skills"][key] = unique_list(data["skills"][key])[:6]

    data["experience"] = data["experience"][:3]
    for entry in data["experience"]:
        entry["bullets"] = [limit_words(bullet, 22) for bullet in entry.get("bullets", [])[:2]]

    data["projects"] = data["projects"][:2]
    for project in data["projects"]:
        project["bullets"] = [limit_words(bullet, 20) for bullet in project.get("bullets", [])[:1]]

    data["education"] = data["education"][:1]

    return data

def flatten_for_existing_routes(data):
    skills_flat = []

    for label, items in data["skills"].items():
        if items:
            skills_flat.append(label.replace("_", " ").title() + ": " + ", ".join(items))

    exp_flat = []
    for entry in data["experience"]:
        header = " | ".join(filter(None, [
            entry.get("company"),
            entry.get("title"),
            entry.get("location"),
            entry.get("dates")
        ]))
        exp_flat.append(header)
        exp_flat.extend(entry.get("bullets", []))

    project_flat = []
    for project in data["projects"]:
        header = " | ".join(filter(None, [
            project.get("name"),
            project.get("tech_stack")
        ]))
        project_flat.append(header)
        project_flat.extend(project.get("bullets", []))

    edu_flat = []
    for edu in data["education"]:
        line = " | ".join(filter(None, [
            edu.get("school"),
            edu.get("degree"),
            edu.get("location"),
            edu.get("dates")
        ]))
        edu_flat.append(line)
        edu_flat.extend(edu.get("details", []))

    return {
        "summary": data["summary"],
        "skills": skills_flat,
        "experience": exp_flat,
        "projects": project_flat,
        "education": edu_flat
    }

def build_fallback_data(full_name, target_role, fallback):
    return {
        "summary": fallback.get("summary", ""),
        "skills": {
            "languages": fallback.get("skills", []),
            "backend": [],
            "frontend": [],
            "databases": [],
            "cloud_devops": [],
            "ai_tools": [],
            "practices": []
        },
        "experience": [{
            "company": "Professional Experience",
            "title": "Software Engineer",
            "location": "",
            "dates": "",
            "bullets": fallback.get("experience", [])[:3]
        }],
        "projects": [{
            "name": "Software Engineering Project",
            "tech_stack": "",
            "bullets": fallback.get("projects", [])[:2]
        }],
        "education": [{
            "school": fallback.get("education", ["New York University"])[0] if fallback.get("education") else "New York University",
            "degree": fallback.get("education", ["", "Master of Science, Computer Engineering"])[1] if len(fallback.get("education", [])) > 1 else "Master of Science, Computer Engineering",
            "location": "",
            "dates": "",
            "details": []
        }]
    }

def compose_resume_text(data):
    parts = []

    parts.append("SUMMARY\n" + data["summary"])

    skill_lines = []
    for label, items in data["skills"].items():
        if items:
            skill_lines.append(label.replace("_", " ").title() + ": " + ", ".join(items))
    parts.append("SKILLS\n" + "\n".join(skill_lines))

    exp_lines = []
    for entry in data["experience"]:
        exp_lines.append(" | ".join(filter(None, [
            entry.get("company"),
            entry.get("title"),
            entry.get("location"),
            entry.get("dates")
        ])))
        exp_lines.extend("- " + bullet for bullet in entry.get("bullets", []))
    parts.append("EXPERIENCE\n" + "\n".join(exp_lines))

    project_lines = []
    for project in data["projects"]:
        project_lines.append(" | ".join(filter(None, [
            project.get("name"),
            project.get("tech_stack")
        ])))
        project_lines.extend("- " + bullet for bullet in project.get("bullets", []))
    parts.append("PROJECTS\n" + "\n".join(project_lines))

    edu_lines = []
    for edu in data["education"]:
        edu_lines.append(" | ".join(filter(None, [
            edu.get("school"),
            edu.get("degree"),
            edu.get("location"),
            edu.get("dates")
        ])))
        edu_lines.extend("- " + detail for detail in edu.get("details", []))
    parts.append("EDUCATION\n" + "\n".join(edu_lines))

    return "\n\n".join(parts)

def build_cover_letter(full_name, target_role, data):
    return f"""Dear Hiring Manager,

I am excited to apply for the {target_role} role. My background includes backend engineering, API development, cloud deployment, database optimization, and full-stack software delivery.

I would appreciate the opportunity to discuss how my experience can contribute to your team.

Sincerely,
{full_name}"""

def unique_list(items):
    result = []
    seen = set()

    for item in items or []:
        text = clean_text(item).lstrip("-•* ").strip()
        key = text.lower()

        if text and key not in seen:
            result.append(text)
            seen.add(key)

    return result

def limit_words(text, max_words):
    words = clean_text(text).split()

    if len(words) <= max_words:
        return " ".join(words)

    return " ".join(words[:max_words]).rstrip(".,;") + "."

def clean_text(value):
    text = str(value or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text
