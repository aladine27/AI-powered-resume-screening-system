from docx import Document  # pip install python-docx
from pathlib import Path
import json

def read_docx(file_path):
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs if para.text.strip() != ""])
    return text

# Dossier contenant tes fichiers Word
docx_folder = Path(r"C:\Users\MSI\Desktop\resume_filter\CV")

# Dictionnaire pour stocker les contenus
results = {}

# Lecture de tous les .docx du dossier
for docx_file in docx_folder.glob("*.docx"):
    try:
        content = read_docx(docx_file)
        results[docx_file.name] = content
    except Exception as e:
        results[docx_file.name] = {"error": str(e)}

# Affichage JSON
print(json.dumps(results, ensure_ascii=False, indent=2))
