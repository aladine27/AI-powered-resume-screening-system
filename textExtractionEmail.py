import os
from pathlib import Path
from PIL import Image, ImageDraw
from pdf2image import convert_from_path
import docx2txt
import pytesseract
import re

# Tes deux fonctions
def convert_to_images(file_path, output_folder="temp_images"):
    os.makedirs(output_folder, exist_ok=True)
    ext = Path(file_path).suffix.lower()
    image_paths = []

    if ext == ".pdf":
        images = convert_from_path(file_path)
        for i, img in enumerate(images):
            img_path = os.path.join(output_folder, f"page_{i+1}.png")
            img.save(img_path, "PNG")
            image_paths.append(img_path)

    elif ext in [".doc", ".docx"]:
        raw_text = docx2txt.process(file_path)
        if raw_text:
            image = Image.new('RGB', (1000, 800), color=(255, 255, 255))
            draw = ImageDraw.Draw(image)
            draw.text((20, 20), raw_text, fill=(0, 0, 0))
            img_path = os.path.join(output_folder, f"doc_text.png")
            image.save(img_path)
            image_paths.append(img_path)

    return image_paths

def extract_email_phrases_from_images(image_paths):
    phrases_with_email = []
    for img_path in image_paths:
        try:
            text = pytesseract.image_to_string(Image.open(img_path), lang='fra+eng')
            lines = text.split("\n")
            for line in lines:
                if "@" in line and re.search(r'\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b', line):
                    phrases_with_email.append(line.strip())
        except Exception as e:
            print(f"Erreur OCR pour {img_path}: {e}")
    return phrases_with_email
# Test avec un vrai fichier
if __name__ == "__main__":
    chemin_cv = "cv_uploads/sana_Missaoui_Cv.docx"  # ⚠️ remplace par le chemin réel d’un de tes fichiers PDF ou DOCX
    images = convert_to_images(chemin_cv)
    print(f"Images générées : {images}")

    emails = extract_email_phrases_from_images(images)
    print("\nEmails extraits :")
    for phrase in emails:
        print("-", phrase)