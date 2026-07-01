import re
import uuid
import subprocess
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from app.config import OUTPUT_DIR, LATEX_TIMEOUT_SECONDS

TEMPLATE_DIR = Path("/app/app/templates")

LATEX_SPECIAL_CHARS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}"
}

def sanitize_text(value):
    text = str(value or "")

    replacements = {
        "•": "-",
        "–": "-",
        "—": "-",
        "“": "\"",
        "”": "\"",
        "‘": "'",
        "’": "'",
        "\xa0": " ",
        "→": "->",
        "←": "<-",
        "≤": "<=",
        "≥": ">=",
        "×": "x",
        "✓": "check",
        "✔": "check"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

def escape_latex(value):
    text = sanitize_text(value)
    return "".join(LATEX_SPECIAL_CHARS.get(char, char) for char in text)

def compile_pdf(template_name, data, output_prefix):
    session_id = str(uuid.uuid4())
    work_dir = OUTPUT_DIR / session_id
    work_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    env.filters["latex"] = escape_latex

    template = env.get_template(template_name)
    tex_content = template.render(**data)

    tex_file = work_dir / f"{output_prefix}.tex"
    tex_file.write_text(tex_content, encoding="utf-8")

    result = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", tex_file.name],
        cwd=str(work_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=LATEX_TIMEOUT_SECONDS,
        check=False
    )

    pdf_file = work_dir / f"{output_prefix}.pdf"

    if not pdf_file.exists():
        log_output = result.stdout[-2500:] if result.stdout else "LaTeX PDF generation failed"
        raise RuntimeError(log_output)

    return str(pdf_file.relative_to(OUTPUT_DIR))
