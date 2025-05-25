import os
from pathlib import Path
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import PyPDF2
import spacy
from docx import Document
from sentence_transformers import SentenceTransformer, util
import json

# === Configurations Tesseract ===
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

# === Modèles NLP ===
nlp = spacy.load('xx_ent_wiki_sm')  # pour entités et n-grams
bert_model = SentenceTransformer('all-MiniLM-L6-v2')  # SBERT léger

# === Fonctions de lecture ===
def read_pdf(file_path):
    text = ""
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
    except Exception:
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
        except Exception:
            pass
    return text


def read_docx(file_path):
    text = ""
    try:
        doc = Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except Exception:
        pass
    return text


def read_image(file_path):
    try:
        return pytesseract.image_to_string(Image.open(file_path), lang='fra')
    except Exception:
        return ""

# === Extraction de compétences et candidats ===
def load_skills(json_path: str) -> set[str]:
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    return {
        skill.lower()
        for skills_list in data.values()
        for skill in skills_list
    }


def extract_candidates(doc, max_ngram: int = 4):
    # Entités nommées
    for ent in doc.ents:
        yield ent.text.lower()
    # n-grams
    tokens = [tok.text for tok in doc if not tok.is_punct and not tok.is_space]
    for n in range(1, max_ngram + 1):
        for i in range(len(tokens) - n + 1):
            yield " ".join(tokens[i : i + n]).lower()

# === Matching BERT ===
def match_skills_bert(text: str, job_skills: list[str], threshold: float = 0.7) -> set[str]:
    doc = nlp(text)
    candidates = list(set(extract_candidates(doc)))
    candidates_clean = [cand.strip() for cand in candidates if len(cand) > 2]

    # Encoder
    emb_cand = bert_model.encode(candidates_clean, convert_to_tensor=True)
    emb_skills = bert_model.encode(job_skills, convert_to_tensor=True)
    cosine_sim = util.cos_sim(emb_skills, emb_cand)

    matched = set()
    for i, skill in enumerate(job_skills):
        for j, _ in enumerate(candidates_clean):
            if cosine_sim[i][j] > threshold:
                matched.add(skill)
                break
    return matched

# === Pipeline complet pour un fichier ===
def process_file(file_path: Path, job_skills: list[str]) -> tuple[Path, set[str]]:
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        text = read_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        text = read_docx(file_path)
    elif ext in [".png", ".jpg", ".jpeg"]:
        text = read_image(file_path)
    else:
        return file_path, set()

    # Matching sémantique
    matched = match_skills_bert(text, job_skills)
    return file_path, matched

# === Traitement d'un dossier complet ===
def process_folder(folder_path: str, job_json: str, threshold: float = 0.7) -> dict:
    folder = Path(folder_path)
    job_skills = [s.strip().lower() for s in (
        # Exemple statique ou depuis JSON
        # sinon remplacer par load_skills(json_path)
        load_skills(job_json)
    )]
    results = {}
    for file_path in folder.iterdir():
        if file_path.is_file():
            path, skills = process_file(file_path, job_skills)
            results[str(path)] = skills
    return results

if __name__ == "__main__":
    CV_FOLDER = r"CV/"
    JOB_JSON = r"C:/Users/MSI/Desktop/resume_filter/job.json"

    all_results = process_folder(CV_FOLDER, JOB_JSON)
    for path, skills in all_results.items():
        print(f"{path}: {', '.join(skills) if skills else 'Aucun match'}")
