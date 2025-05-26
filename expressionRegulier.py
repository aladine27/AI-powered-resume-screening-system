import os
from pathlib import Path
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import PyPDF2
import spacy
from docx import Document
from itertools import chain, islice
import re 
import json
from sentence_transformers import SentenceTransformer, util
# === Configurations Tesseract ===
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

# === Chargement du modèle spaCy français permet la compréhension du text automatique ===
nlp = spacy.load('xx_ent_wiki_sm')
# Charger un modèle SBERT léger (très rapide et performant)
bert_model = SentenceTransformer('all-MiniLM-L6-v2')  # léger mais précis

# === Fonctions de lecture ===
def read_pdf(file_path):
    text = ""
    try:
        with fitz.open(file_path) as doc:
            for page_num, page in enumerate(doc, start=1):
                text += page.get_text()
    except Exception as e:
        print(f"Erreur lors de la lecture PDF avec fitz : {e}")
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text()
        except Exception as e2:
            print(f"Erreur avec PyPDF2 : {e2}")
    return text

def read_docx(file_path):
    text = ""
    try:
        doc = Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except Exception as e:
        print(f"Erreur lors de la lecture DOCX : {e}")
    return text

def read_image(file_path):
    try:
        return pytesseract.image_to_string(Image.open(file_path), lang='fra')
        
    except Exception as e:
        print(f"Erreur OCR image : {e}")
        return ""

def load_skills(json_path: str) -> set[str]:
    """
    Charge le JSON de compétences et renvoie un set de tous les skills en minuscules.
    """
    with open(json_path, encoding="utf‑8") as f:
        data = json.load(f)
    # aplatir toutes les listes
    skills = set(
        skill.lower()
        for skills_list in data.values()
        for skill in skills_list
    )
    return skills
#fonction qui extraire les skils du cv
def extract_candidates(doc, max_ngram: int = 4):
    """
    Génère tous les n‑grams (jusqu'à max_ngram) et les entités nommées.
    On combine entités + n‑grams pour couvrir les compétences multi‑mots.
    """
    # entités
    for ent in doc.ents:
        yield ent.text.lower()
    # n‑grams sur tokens (sans ponctuation ni espaces seuls)
    tokens = [tok.text for tok in doc if not tok.is_punct and not tok.is_space]
    for n in range(1, max_ngram + 1):
        for i in range(len(tokens) - n + 1):
            yield " ".join(tokens[i : i + n]).lower()
            
    #retourne les skillls de candidate qui se trouve dans json et cv          
def match_skills(text: str, skills_set: set[str]) -> set[str]:
    """
    Retourne l'intersection entre les candidats extraits et le set de skills.
    """
    doc = nlp(text)
    candidates = extract_candidates(doc)
    # intersection
    matched = {cand for cand in candidates if cand in skills_set}
    return matched
#semilaritéej
job_skills="python , java  , ML,scrum,business analyst,mysql,mongodb,angular,React,pilot,cuisinier,test"
job_skills=job_skills.split(",")
def match_skills_bert(text: str, job_skills: set[str], threshold: float = 0.7) -> set[str]:

    #Compare les compétences extraites avec les compétences attendues via BERT similarity.
    
    doc = nlp(text)
    candidates = list(set(extract_candidates(doc)))

    # Nettoyage des données 
    # skills extraites du CV
    candidates_clean = [cand.strip().lower() for cand in candidates if len(cand) > 2]
    
    # skills du offre d'emploi
    skills_list = list(job_skills)

    # Encoder les phrases
    candidate_embeddings = bert_model.encode(candidates_clean, convert_to_tensor=True)
    skills_embeddings = bert_model.encode(skills_list, convert_to_tensor=True)

    matched_skills = set()

    # Similarité cosine entre chaque skill du offre et cv
    cosine_sim = util.cos_sim(skills_embeddings, candidate_embeddings)

    for skill_idx, skill in enumerate(skills_list):
        for cand_idx, candidate in enumerate(candidates_clean):
            if cosine_sim[skill_idx][cand_idx] > threshold:
                matched_skills.add(skill)
                break  # on peut stopper dès qu’un match est trouvé

    return matched_skills 
# Fonction pour extraire l'email à partir du texte
def extract_email(text):
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else None
# === Fonction de traitement complet ===
def process_file(file_path):
    ext = Path(file_path).suffix.lower()
    text = ""

    if ext == ".pdf":
      #  print(f"Lecture PDF : {file_path}")
        text = read_pdf(file_path)

    elif ext in [".docx", ".doc"]:
       # print(f"Lecture DOCX : {file_path}")
        text = read_docx(file_path)

    elif ext in [".png", ".jpg", ".jpeg"]:
      #  print(f"Lecture IMAGE : {file_path}")
        text = read_image(file_path)

    else:
        print("Type de fichier non supporté.")
        return

    # Analyse du texte avec spaCy
    if text:
       # print("\n=== Analyse NLP ===")
        doc = nlp(text)

       # print("\n--- Entités nommées ---")
        for ent in doc.ents:
            print(f"{ent.text} ({ent.label_})")

       # print("\n--- Tokens ---")
        for token in doc[:30]:  # Afficher les 30 premiers tokens
            print(f"{token.text} -> {token.pos_}")
    else:
        print("Aucun texte extrait pour traitement.")
    skills_set = load_skills(r"C:\Users\MSI\Desktop\resume_filter\job.json")
    matched_skills = match_skills(text, skills_set)
    matched_skills_bert = match_skills_bert(' '.join(matched_skills), job_skills)
    print("\n--- skills ---")
    for skill in  matched_skills_bert:
        print(skill)    
    return  matched_skills_bert

# === Program principale ===
if __name__ == "__main__":
   test_path = r"CV_uploads/CV_Anglais_Ala.pdf"
   process_file(test_path)