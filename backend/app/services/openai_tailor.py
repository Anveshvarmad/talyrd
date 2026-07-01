import json
import re
from openai import OpenAI
from app.config import OPENAI_API_KEY, OPENAI_MODEL

def tailor_resume_with_openai(
    full_name,
    target_role,
    resume_text,
    job_description,
    ats_analysis
):
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is missing in .env")

    client = OpenAI(api_key=OPENAI_API_KEY)

    instructions = """
You are Talyrd, an AI resume tailoring assistant.

Your task:
- Rewrite the candidate's resume content for the target role.
- Generate a matching cover letter.
- Improve ATS alignment using the job description.
- Keep all content truthful.

Strict rules:
- Do not invent employers, education, dates, certifications, projects, tools, metrics, or skills.
- Only use information supported by the original resume.
- If a job keyword is missing but not supported by the resume, mention it only in recommendations, not as a claim.
- Keep the resume ATS-friendly, concise, and professional.
- Avoid keyword stuffing.
- Return valid JSON only.
"""

    payload = {
        "full_name": full_name,
        "target_role": target_role,
        "original_resume": resume_text,
        "job_description": job_description,
        "ats_analysis": ats_analysis,
        "json_schema": {
            "tailored_resume_text": "ATS-friendly rewritten resume text with clear sections",
            "cover_letter_text": "Professional cover letter for the target role",
            "improvement_summary": "Short explanation of what changed and why"
        }
    }

    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=instructions,
        input=json.dumps(payload),
        temperature=0.2,
        max_output_tokens=3000
    )

    output_text = response.output_text.strip()
    data = parse_json(output_text)

    return {
        "tailored_resume_text": clean_text(data.get("tailored_resume_text", "")),
        "cover_letter_text": clean_text(data.get("cover_letter_text", "")),
        "improvement_summary": clean_text(data.get("improvement_summary", ""))
    }

def parse_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("OpenAI response was not valid JSON")
        return json.loads(match.group(0))

def clean_text(value):
    return str(value or "").strip()
