from io import BytesIO

from flask import Flask, render_template, request, send_file

from ai_writer import (
    AIConfigurationError,
    AIServiceError,
    improve_cv,
    write_cover_letter,
)
from fpdf import FPDF

app = Flask(__name__, template_folder="templates")

VALID_THEMES = {"professional", "modern", "dark"}
CV_FIELDS = (
    "name",
    "email",
    "phone",
    "location",
    "linkedin",
    "git_profile",
    "education",
    "experience",
    "skills",
    "certification",
    "hobbies",
)
AI_INPUT_LIMIT = 30000


class CVPDF(FPDF):
    def __init__(self, theme, auto_page_break=False):
        self.theme = theme
        super().__init__()
        if theme == "modern":
            self.set_margins(68, 18, 14)
        else:
            self.set_margins(18, 18, 18)
        self.set_auto_page_break(auto=auto_page_break, margin=16)

    def header(self):
        if self.theme == "modern":
            self.set_fill_color(234, 243, 251)
            self.rect(0, 0, self.w, self.h, style="F")
            self.set_fill_color(255, 255, 255)
            self.rect(7, 8, self.w - 14, self.h - 16, style="F")
            self.set_fill_color(31, 78, 121)
            self.rect(7, 8, 60, self.h - 16, style="F")
        elif self.theme == "dark":
            self.set_fill_color(34, 34, 34)
            self.rect(0, 0, self.w, self.h, style="F")
            self.set_fill_color(48, 52, 58)
            self.rect(7, 8, self.w - 14, self.h - 16, style="F")
        else:
            self.set_fill_color(255, 255, 255)
            self.rect(0, 0, self.w, self.h, style="F")
        self.set_y(18)


def build_summary(experience, skills):
    summary_parts = []

    if "customer" in experience.lower():
        summary_parts.append("Experienced in delivering excellent customer service.")
    if "team" in experience.lower():
        summary_parts.append(
            "Strong team player with experience working in collaborative environments."
        )
    if "training" in experience.lower():
        summary_parts.append("Experienced in mentoring and supporting colleagues.")
    if "python" in skills.lower():
        summary_parts.append("Possesses programming experience using Python.")
    if "html" in skills.lower():
        summary_parts.append("Skilled in web development technologies.")
    if "testing" in skills.lower():
        summary_parts.append(
            "Knowledgeable in software testing and quality assurance practices."
        )
    if "communication" in skills.lower():
        summary_parts.append("Demonstrates strong communication skills.")

    return " ".join(summary_parts)


def _cv_fields_from_request():
    return {key: request.form.get(key, "").strip() for key in CV_FIELDS}


def _render_cv_result(fields, theme, summary, **extra_context):
    skills_list = [skill.strip() for skill in fields["skills"].split(",") if skill.strip()]
    context = {
        **fields,
        "theme": theme,
        "skills_list": skills_list,
        "summary": summary,
    }
    context.update(extra_context)
    return render_template("result.html", **context)


@app.route("/download", methods=["POST"])
def download_pdf():
    fields = _cv_fields_from_request()
    summary = request.form.get("summary", "").strip() or build_summary(
        fields["experience"], fields["skills"]
    )
    theme = request.form.get("theme", "professional")
    if theme not in VALID_THEMES:
        theme = "professional"
    pdf = None
    for scale in (1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6):
        pdf, sidebar_bottom = _render_cv_pdf(fields, summary, theme, scale)
        content_bottom = max(pdf.get_y(), sidebar_bottom)
        if content_bottom <= pdf.h - pdf.b_margin:
            break

    if pdf is None:
        raise RuntimeError("Could not create the CV PDF.")
    if content_bottom > pdf.h - pdf.b_margin:
        # Keep long CVs readable and complete instead of clipping or duplicating their content.
        pdf, _ = _render_cv_pdf(
            fields, summary, theme, scale=0.6, auto_page_break=True
        )

    pdf_bytes = bytes(pdf.output())
    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="cv.pdf",
    )


def _render_cv_pdf(fields, summary, theme, scale, auto_page_break=False):
    pdf = CVPDF(theme, auto_page_break=auto_page_break)
    pdf.add_page()
    if theme == "dark":
        pdf.set_text_color(243, 245, 247)
        heading_color = (169, 210, 242)
    else:
        pdf.set_text_color(34, 41, 48)
        heading_color = (31, 78, 121)

    sidebar_bottom = 0
    if theme == "modern":
        sidebar_bottom = _pdf_sidebar(pdf, fields, scale)
        pdf.set_xy(68, 18)
        pdf.set_text_color(31, 78, 121)

    pdf.set_font("Arial", style="B", size=max(10, round(20 * scale)))
    _pdf_multi_cell(pdf, 12 * scale, fields["name"] or "CV", wrapmode="CHAR")
    pdf.ln(2 * scale)
    pdf.set_font("Arial", size=max(7, round(10 * scale)))

    if theme != "modern":
        contact_details = [
            f"Email: {fields['email']}",
            f"Phone: {fields['phone']}",
            f"Location: {fields['location']}",
            f"LinkedIn: {fields['linkedin']}",
            f"Git Profile: {fields['git_profile']}",
        ]
        for detail in contact_details:
            if detail.split(": ", 1)[1]:
                _pdf_multi_cell(pdf, 6 * scale, detail, wrapmode="CHAR")
    pdf.ln(3 * scale)

    skills = ", ".join(
        skill.strip() for skill in fields["skills"].split(",") if skill.strip()
    )
    sections = [("Professional Summary", summary)]
    if theme != "modern":
        sections.append(("Skills", skills))
    sections.extend(
        (
            ("Work Experience", fields["experience"]),
            ("Education", fields["education"]),
            ("Certifications", fields["certification"]),
            ("Hobbies and Interests", fields["hobbies"]),
        )
    )
    for title, content in sections:
        if content.strip():
            pdf.set_text_color(*heading_color)
            pdf.set_font("Arial", style="B", size=max(8, round(13 * scale)))
            _pdf_multi_cell(pdf, 8 * scale, title)
            if theme == "dark":
                pdf.set_text_color(214, 220, 226)
            else:
                pdf.set_text_color(34, 41, 48)
            pdf.set_font("Arial", size=max(6, round(11 * scale)))
            _pdf_multi_cell(pdf, 6 * scale, content)
            pdf.ln(3 * scale)

    return pdf, sidebar_bottom


def _pdf_safe_text(text):
    replacements = {
        "•": "-",
        "‣": "-",
        "▪": "-",
        "◦": "-",
        "✓": "[x]",
        "✔": "[x]",
        "–": "-",
        "—": "-",
        "−": "-",
        "→": "->",
        "←": "<-",
        "↔": "<->",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "…": "...",
        "\u00a0": " ",
        "€": "EUR",
        "£": "GBP",
        "©": "(c)",
        "®": "(R)",
        "™": "(TM)",
    }
    for character, replacement in replacements.items():
        text = text.replace(character, replacement)
    return (
        text.encode("ascii", "ignore").decode("ascii")
        if any(ord(character) > 127 for character in text)
        else text
    )


def _pdf_multi_cell(pdf, height, text, wrapmode="WORD"):
    pdf.multi_cell(
        0,
        height,
        _pdf_safe_text(text),
        new_x="LMARGIN",
        new_y="NEXT",
        wrapmode=wrapmode,
    )


def _pdf_sidebar(pdf, fields, scale):
    sidebar_x = 11
    sidebar_width = 52
    y = 20
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(sidebar_x, y)
    contact_details = [
        ("Email", fields["email"]),
        ("Phone", fields["phone"]),
        ("Location", fields["location"]),
        ("LinkedIn", fields["linkedin"]),
        ("Git Profile", fields["git_profile"]),
    ]
    contact_details = [(label, value) for label, value in contact_details if value]
    if contact_details:
        pdf.set_font("Arial", style="B", size=max(7, round(11 * scale)))
        pdf.multi_cell(
            sidebar_width, 6 * scale, "CONTACT", new_x="LEFT", new_y="NEXT"
        )
        y = pdf.get_y() + 3 * scale
        pdf.set_font("Arial", size=max(6, round(8 * scale)))
        for label, value in contact_details:
            pdf.set_xy(sidebar_x, y)
            pdf.multi_cell(
                sidebar_width,
                4.5 * scale,
                _pdf_safe_text(f"{label}: {value}"),
                new_x="LEFT",
                new_y="NEXT",
                wrapmode="CHAR",
            )
            y = pdf.get_y() + 2 * scale

    skills = [skill.strip() for skill in fields["skills"].split(",") if skill.strip()]
    if skills:
        y += 4 * scale
        pdf.set_xy(sidebar_x, y)
        pdf.set_font("Arial", style="B", size=max(7, round(11 * scale)))
        pdf.multi_cell(
            sidebar_width, 6 * scale, "SKILLS", new_x="LEFT", new_y="NEXT"
        )
        y = pdf.get_y() + 3 * scale
        pdf.set_font("Arial", size=max(6, round(8 * scale)))
        for skill in skills:
            pdf.set_xy(sidebar_x, y)
            pdf.multi_cell(
                sidebar_width,
                4.5 * scale,
                _pdf_safe_text(f"- {skill}"),
                new_x="LEFT",
                new_y="NEXT",
                wrapmode="WORD",
            )
            y = pdf.get_y() + scale

    if fields["hobbies"]:
        y += 4 * scale
        pdf.set_xy(sidebar_x, y)
        pdf.set_font("Arial", style="B", size=max(7, round(11 * scale)))
        pdf.multi_cell(
            sidebar_width, 6 * scale, "HOBBIES AND INTERESTS",
            new_x="LEFT", new_y="NEXT"
        )
        y = pdf.get_y() + 3 * scale
        pdf.set_font("Arial", size=max(6, round(8 * scale)))
        pdf.set_xy(sidebar_x, y)
        pdf.multi_cell(
            sidebar_width, 4.5 * scale, _pdf_safe_text(fields["hobbies"]),
            new_x="LEFT", new_y="NEXT", wrapmode="WORD"
        )
    return pdf.get_y()


@app.route("/cover-letter", methods=["POST"])
def cover_letter():
    fields = _cv_fields_from_request()
    summary = request.form.get("summary", "").strip()
    job_title = request.form.get("job_title", "").strip()
    company = request.form.get("company", "").strip()
    job_description = request.form.get("job_description", "").strip()
    instructions = request.form.get("instructions", "").strip()
    ai_error = None

    if not job_title:
        ai_error = "Enter the job title to tailor your cover letter."
    elif (
        sum(map(len, fields.values()))
        + len(summary)
        + len(job_title)
        + len(company)
        + len(job_description)
        + len(instructions)
        > AI_INPUT_LIMIT
    ):
        ai_error = "The CV and job details are too long. Shorten them and try again."
    else:
        fields["summary"] = summary
        try:
            letter = write_cover_letter(
                fields, job_title, company, job_description, instructions
            )
        except (AIConfigurationError, AIServiceError) as error:
            ai_error = str(error)
        else:
            return render_template(
                "cover_letter.html",
                name=fields["name"],
                email=fields["email"],
                phone=fields["phone"],
                location=fields["location"],
                paragraphs=[
                    paragraph.strip()
                    for paragraph in letter.split("\n\n")
                    if paragraph.strip()
                ],
            )

    theme = request.form.get("theme", "professional")
    if theme not in VALID_THEMES:
        theme = "professional"
    return _render_cv_result(
        fields,
        theme,
        summary,
        ai_error=ai_error,
        job_title=job_title,
        company=company,
        job_description=job_description,
        instructions=instructions,
    )


@app.route("/")
def home():
    return render_template("landing.html")

@app.route("/builder")
def builder():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    theme = request.form.get("theme", "professional")
    if theme not in VALID_THEMES:
        theme = "professional"
    fields = _cv_fields_from_request()
    summary = request.form.get("summary", "").strip() or build_summary(
        fields["experience"], fields["skills"]
    )
    return _render_cv_result(fields, theme, summary)


@app.route("/improve-cv", methods=["POST"])
def improve_cv_route():
    fields = _cv_fields_from_request()
    summary = request.form.get("summary", "").strip()
    theme = request.form.get("theme", "professional")
    if theme not in VALID_THEMES:
        theme = "professional"
    target_role = request.form.get("target_role", "").strip()
    job_description = request.form.get("job_description", "").strip()

    if (
        sum(map(len, fields.values()))
        + len(summary)
        + len(target_role)
        + len(job_description)
        > AI_INPUT_LIMIT
    ):
        return _render_cv_result(
            fields,
            theme,
            summary or build_summary(fields["experience"], fields["skills"]),
            ai_error="The CV and job details are too long. Shorten them and try again.",
            target_role=target_role,
            job_description=job_description,
        )

    fields["summary"] = summary
    try:
        improvements = improve_cv(fields, target_role, job_description)
    except (AIConfigurationError, AIServiceError) as error:
        return _render_cv_result(
            fields,
            theme,
            summary or build_summary(fields["experience"], fields["skills"]),
            ai_error=str(error),
            target_role=target_role,
            job_description=job_description,
        )

    return render_template(
        "improved_cv.html",
        fields=fields,
        theme=theme,
        improvements=improvements,
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0")