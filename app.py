import os
import requests
from flask import Flask, render_template, request, jsonify, send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

app = Flask(__name__)

# Get API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
API_URL = "https://api.groq.com/openai/v1/chat/completions"

generated_sop = None  # store latest SOP text


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate_sop", methods=["POST"])
def generate_sop():
    global generated_sop

    data = request.json
    name = data.get("name")
    age = data.get("age")
    country = data.get("country")
    course = data.get("course")
    university = data.get("university")
    background = data.get("background")
    goals = data.get("goals")

    # Build SOP prompt
    prompt = f"""
    Write a well-structured Statement of Purpose (SOP) for a student.

    Details:
    - Name: {name}
    - Age: {age}
    - Applying to: {country}
    - Desired Course: {course}
    - University: {university}
    - Educational Background: {background}
    - Future Goals: {goals}

    The SOP should be formal, engaging, and highlight motivation, academic background, and career aspirations.
    """

    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama3-8b-8192",  # ✅ Groq-supported model
            "messages": [{"role": "user", "content": prompt}],
        }

        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        generated_sop = result["choices"][0]["message"]["content"].strip()
        return jsonify({"sop": generated_sop})

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/download_pdf", methods=["GET"])
def download_pdf():
    global generated_sop
    if not generated_sop:
        return "No SOP generated yet!", 400

    pdf_filename = "generated_sop.pdf"

    # Create formatted PDF
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    for para in generated_sop.split("\n\n"):
        story.append(Paragraph(para.strip(), styles["Normal"]))
        story.append(Spacer(1, 12))

    doc.build(story)

    return send_file(pdf_filename, as_attachment=True)


if __name__ == "__main__":
    if not GROQ_API_KEY:
        raise ValueError("❌ GROQ_API_KEY is missing! Please set it in environment variables.")
    app.run(debug=True)
