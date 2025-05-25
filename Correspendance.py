import re
import spacy
import json
import PyPDF2
import os
from docx import Document

from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract


# === Configurations Tesseract ===
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"


# Charger le modèle spaCy pour l'analyse de texte
nlp = spacy.load('fr_core_news_sm')

# Charger le dictionnaire de mappage des compétences à partir d'un fichier JSON
with open('job2.json', 'r', encoding='utf-8') as f:
    competences_mapping = json.load(f)

# Fonction pour lire le contenu d'un fichier PDF
def read_pdf(file_path):
    pdf_reader = PyPDF2.PdfReader(file_path)
    text = ""
    for page in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page].extract_text()
    return text

# Fonction pour lire le contenu d'un fichier DOCX
def read_docx(file_path):
    doc = Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text
def read_image(file_path):
    try:
        return pytesseract.image_to_string(Image.open(file_path), lang='fra')
    except Exception as e:
        print(f"Erreur OCR image : {e}")
        return ""

# Fonction pour trouver la section "Compétences" dans le texte du CV
def find_skills_section(cv_text):
    patterns = r'(Compétences|Skills|Expertises|Savoir-Faire|Qualifications|Connaissances|Aptitudes|Proficiencies|technical skills)'
    matches = list(re.finditer(patterns, cv_text, re.IGNORECASE))
    
    if matches:
        sections = []
        for match in matches:
            start = match.start()
            end = cv_text.find('\n\n', start)
            if end == -1:
                end = len(cv_text)
            sections.append(cv_text[start:end])
            print(f"Match found: {cv_text[start:end][:100]}")  # Print the first 100 characters of the matched section
        
        return sections[0] if sections else None
    else:
        return None

# Fonction pour extraire les compétences de la section "Compétences"
def extract_skills(skills_section):
    doc = nlp(skills_section)
    skills = [chunk.text.strip() for chunk in doc.noun_chunks]
    return skills

""" # Fonction pour normaliser les compétences
def normalize_skills(skills):
    normalized_skills = []
    for skill in skills:
        normalized_skill = competences_mapping.get(skill.lower(), skill)
        normalized_skills.append(normalized_skill)
    return normalized_skills """

# Fonction pour traiter le CV et extraire les compétences
def process_cv(file_path):
    if file_path.endswith('.pdf'):
        cv_text = read_pdf(file_path)
    elif file_path.endswith('.docx'):
        cv_text = read_docx(file_path)
    elif file_path.endswith(('.png', '.jpg', '.jpeg', '.avif')):
        cv_text = read_image(file_path)
    else:
        raise ValueError("Unsupported file format")

    #print(f"Extracted CV text: {cv_text[:1000]}")  # Debug: Print the first 1000 characters of the CV text

    skills_section = find_skills_section(cv_text)

    if skills_section:
        extracted_skills = extract_skills(skills_section)
        print(f"Extracted Skills: {extracted_skills}")  # Debug: Print the extracted skills
        #normalized_skills = normalize_skills(extracted_skills)
        #print(f"Normalized Skills: {normalized_skills}")  # Debug: Print the normalized skills
        return extracted_skills
    else:
        print("Skills section not found")
        return []
# === Program principale ===
if __name__ == "__main__":
    test_path = r"CV\CV-Bilel_Naffeti.pdf"
    process_cv(test_path)