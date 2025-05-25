from flask import Flask, request, jsonify
import os
from pathlib import Path
from expressionRegulier import *
import re

app = Flask(__name__)

# Dossier contenant les CVs
UPLOAD_FOLDER = 'cv_uploads'

# Fonction pour extraire l'email à partir du texte
def extract_email(text):
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else None

@app.route('/match_skills', methods=['POST'])
def match_skills_api():
    data = request.get_json()

    if not data or 'requirements' not in data:
        return jsonify({"error": "Missing 'requirements' in request"}), 400

    job_skills_raw = data['requirements']

    if isinstance(job_skills_raw, str):
        job_skills_set = set(skill.strip().lower() for skill in job_skills_raw.split(","))
    elif isinstance(job_skills_raw, list):
        job_skills_set = set(skill.strip().lower() for skill in job_skills_raw)
    else:
        return jsonify({"error": "'requirements' must be a string or list"}), 400

    result = []

    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        ext = Path(file_path).suffix.lower()

        if ext not in [".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg"]:
            continue

        try:
            text = ""
            if ext == ".pdf":
                text = read_pdf(file_path)
            elif ext in [".docx", ".doc"]:
                text = read_docx(file_path)
            elif ext in [".png", ".jpg", ".jpeg"]:
                text = read_image(file_path)

            if text:
                email = extract_email(text)
                skills_set = load_skills(r"C:\Users\MSI\Desktop\resume_filter\job.json")
                matched = match_skills(text, skills_set)
                matched_bert = match_skills_bert(' '.join(matched), job_skills_set)

                total_job_skills = len(job_skills_set)
                nb_matched = len(matched_bert)
                score = (nb_matched / total_job_skills) * 100 if total_job_skills > 0 else 0

                result.append({
                    "filename": filename,
                    "email": email,
                    "skills_matched": list(matched_bert),
                    "score": round(score, 2)
                })

        except Exception as e:
            result.append({
                "filename": filename,
                "error": str(e),
                "score": 0.0
            })

    # Trier les résultats par score décroissant
    sorted_result = sorted(result, key=lambda x: x.get("score", 0.0), reverse=True)

    # Retourner la liste triée
    return jsonify(sorted_result)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
