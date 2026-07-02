import re
from collections import Counter

STOPWORDS = {
    "and", "or", "the", "a", "an", "to", "of", "in", "for", "with", "on",
    "by", "is", "are", "as", "be", "this", "that", "from", "at", "you",
    "your", "we", "our", "will", "can", "using", "use", "work", "team",
    "role", "job", "candidate", "company", "responsibilities", "requirements",
    "required", "preferred", "must", "should", "plus", "strong", "good",
    "excellent", "ability", "including", "etc", "also", "within", "across",
    "building", "developing", "working", "participate", "contribute",
    "through", "multiple", "deliver", "delivering", "ownership", "sense",
    "urgency", "course", "corrections", "appropriate", "when", "other",
    "successful", "ensure", "engaging", "cross-functionally", "along",
    "surfacing", "risks", "mitigating", "suggesting", "mindset"
}

SKILL_PHRASES = [
    "python", "java", "javascript", "typescript", "react", "next.js",
    "node.js", "flask", "django", "fastapi", "postgresql", "mysql",
    "mongodb", "redis", "docker", "kubernetes", "aws", "azure", "gcp",
    "git", "github", "github actions", "jenkins", "ci/cd", "rest api",
    "rest apis", "microservices", "sql", "nosql", "linux", "api design",
    "software architecture", "unit testing", "pytest", "jest",
    "machine learning", "deep learning", "nlp", "llm", "openai", "rag",
    "langchain", "latex", "pdf generation", "full-stack", "full stack",
    "backend", "frontend", "cloud deployment", "automation", "agile",
    "scrum", "data structures", "algorithms", "monitoring", "logging",
    "metrics", "observability", "devops", "on-call", "incident response",
    "scalability", "resiliency", "test automation", "clean code",
    "maintainable code", "low-latency", "high-throughput", "secure coding",
    "defensive coding", "instrumentation", "deployment", "services",
    "workflows", "code reviews"
]

GENERIC_ACTION_WORDS = {
    "develop", "maintain", "support", "create", "drive", "own", "collaborate",
    "write", "writing", "effective", "efficient", "clean", "paired",
    "programming", "reviews", "automated", "testing", "requirements"
}

SYNONYMS = {
    "rest apis": "rest api",
    "apis": "api",
    "full-stack": "full stack",
    "postgres": "postgresql",
    "k8s": "kubernetes",
    "js": "javascript",
    "ts": "typescript",
    "ml": "machine learning",
    "artificial intelligence": "ai",
    "large language model": "llm",
    "large language models": "llm",
    "ci cd": "ci/cd",
    "continuous integration": "ci/cd",
    "continuous deployment": "ci/cd"
}

def normalize_keyword(keyword):
    keyword = keyword.lower().strip()
    keyword = re.sub(r"\s+", " ", keyword)
    return SYNONYMS.get(keyword, keyword)

def tokenize(text):
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+#./-]*", text.lower())
    clean_tokens = []

    for token in tokens:
        token = normalize_keyword(token)

        if token in STOPWORDS:
            continue

        if token in GENERIC_ACTION_WORDS:
            continue

        if len(token) <= 2:
            continue

        clean_tokens.append(token)

    return clean_tokens

def extract_skill_phrases(text):
    text_lower = text.lower()
    found = []

    for phrase in SKILL_PHRASES:
        if phrase in text_lower:
            normalized = normalize_keyword(phrase)
            if normalized not in found:
                found.append(normalized)

    return found

def extract_keywords(text, limit=30):
    phrase_keywords = extract_skill_phrases(text)

    tokens = tokenize(text)
    token_counts = Counter(tokens)

    frequency_keywords = []
    for token, _ in token_counts.most_common(limit):
        normalized = normalize_keyword(token)
        if normalized not in frequency_keywords:
            frequency_keywords.append(normalized)

    combined = []

    for keyword in phrase_keywords + frequency_keywords:
        if keyword not in combined and keyword not in STOPWORDS:
            combined.append(keyword)

    return combined[:limit]

def analyze_resume_against_job(resume_text, job_description):
    resume_lower = resume_text.lower()

    job_keywords = extract_keywords(job_description, limit=30)
    resume_keywords = extract_keywords(resume_text, limit=60)

    matched_keywords = []
    missing_keywords = []

    for keyword in job_keywords:
        keyword_lower = keyword.lower()

        if keyword_lower in resume_lower or keyword_lower in resume_keywords:
            matched_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)

    ats_score = round((len(matched_keywords) / len(job_keywords)) * 100) if job_keywords else 0

    recommendations = build_recommendations(missing_keywords)

    return {
        "ats_score": ats_score,
        "job_keywords": job_keywords,
        "resume_keywords": resume_keywords,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "recommendations": recommendations
    }

def build_recommendations(missing_keywords):
    if not missing_keywords:
        return [
            "Resume already has strong keyword alignment with this job description."
        ]

    top_missing = missing_keywords[:8]

    return [
        "Add missing keywords only if they truthfully match your experience.",
        "Prioritize these high-value missing keywords: " + ", ".join(top_missing),
        "Place important skills in both the Skills section and relevant Experience or Project bullets.",
        "Avoid keyword stuffing. Use keywords naturally inside achievement-based bullet points."
    ]
