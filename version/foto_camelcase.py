import fitz  # PyMuPDF
import re
import os
from datetime import datetime

# Diretório com os PDFs
input_dir = r'C:\Users\Alexandre\Documents\ER_dados'
output_dir = os.path.join(input_dir, 'fotos_funcionarios')

# Cria o diretório de saída se não existir
os.makedirs(output_dir, exist_ok=True)

# Percorre todos os arquivos PDF no diretório
for filename in os.listdir(input_dir):
    if filename.lower().endswith(".pdf"):
        pdf_path = os.path.join(input_dir, filename)
        print(f"🔍 Processando: {filename}")

        try:
            doc = fitz.open(pdf_path)

            # Extrai texto de todas as páginas para encontrar matrícula e nome
            full_text = ""
            for page in doc:
                full_text += page.get_text()

            # Regex para encontrar matrícula e nome
            match = re.search(r'(\d{4,6})\s+([A-Z\s]{5,})', full_text)
            if not match:
                print("❌ Matrícula e nome não encontrados.")
                doc.close()
                continue

            matricula = match.group(1)
            nome_raw = match.group(2).strip()

            # Converte para CamelCase (primeira letra maiúscula, restante minúscula)
            nome_camel = "_".join(word.capitalize() for word in nome_raw.split())

            # Timestamp atual
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            output_filename = f"{matricula}_{nome_camel}_{timestamp}.jpeg"
            output_path = os.path.join(output_dir, output_filename)

            # Extrai a primeira imagem do PDF
            imagem_salva = False
            for page_index in range(len(doc)):
                images = doc[page_index].get_images(full=True)
                if images:
                    xref = images[0][0]
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n < 5:
                        pix.save(output_path)
                    else:
                        pix_rgb = fitz.Pixmap(fitz.csRGB, pix)
                        pix_rgb.save(output_path)
                        pix_rgb = None
                    imagem_salva = True
                    print(f"✅ Imagem salva: {output_filename}")
                    break

            if not imagem_salva:
                print("❌ Nenhuma imagem encontrada no PDF.")

            doc.close()

        except Exception as e:
            print(f"⚠️ Erro ao processar {filename}: {e}")
