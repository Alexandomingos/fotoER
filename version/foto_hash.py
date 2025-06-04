import fitz  # PyMuPDF
import re
import os
import hashlib
from datetime import datetime

# Diretórios
input_dir = r'C:\Users\Alexandre\Documents\ER_dados'
output_dir = os.path.join(input_dir, 'fotos_funcionarios')
os.makedirs(output_dir, exist_ok=True)

# Função para gerar hash da imagem
def gerar_hash_imagem(pixmap):
    img_bytes = pixmap.tobytes("ppm")
    return hashlib.md5(img_bytes).hexdigest()

# Função para gerar o nome do arquivo com versão
def gerar_nome_arquivo(matricula, nome_camel, data_pdf, versao):
    return f"{matricula}_{nome_camel}_{data_pdf}_v{versao}.jpeg"

# Percorre os PDFs
for filename in os.listdir(input_dir):
    if filename.lower().endswith(".pdf"):
        pdf_path = os.path.join(input_dir, filename)
        print(f"🔍 Processando: {filename}")

        try:
            doc = fitz.open(pdf_path)

            # Extrai texto
            full_text = ""
            for page in doc:
                full_text += page.get_text()

            # Regex para matrícula e nome
            match = re.search(r'(\d{4,6})\s+([A-Z\s]{5,})', full_text)
            if not match:
                print("❌ Matrícula e nome não encontrados.")
                doc.close()
                continue

            matricula = match.group(1)
            nome_raw = match.group(2).strip()
            nome_camel = "_".join(word.capitalize() for word in nome_raw.split())

            # Usa data de modificação do PDF
            mod_timestamp = os.path.getmtime(pdf_path)
            data_pdf = datetime.fromtimestamp(mod_timestamp).strftime("%Y%m%d_%H%M%S")

            imagem_extraida = None
            imagem_hash = None

            # Extrai a primeira imagem
            for page_index in range(len(doc)):
                images = doc[page_index].get_images(full=True)
                if images:
                    xref = images[0][0]
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n >= 5:
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    imagem_extraida = pix
                    imagem_hash = gerar_hash_imagem(pix)
                    break

            if not imagem_extraida or not imagem_hash:
                print("❌ Nenhuma imagem encontrada no PDF.")
                doc.close()
                continue

            # Verifica se já existe imagem com esse hash
            hash_ja_existente = False
            for img_file in os.listdir(output_dir):
                if img_file.lower().endswith(".jpeg"):
                    caminho = os.path.join(output_dir, img_file)
                    try:
                        with open(caminho, "rb") as f:
                            bytes_img = f.read()
                            if hashlib.md5(bytes_img).hexdigest() == imagem_hash:
                                hash_ja_existente = True
                                print(f"⏭️ Imagem idêntica já salva: {img_file}")
                                break
                    except:
                        continue

            if hash_ja_existente:
                doc.close()
                continue

            # Verifica a próxima versão disponível
            versao = 1
            while True:
                nome_arquivo = gerar_nome_arquivo(matricula, nome_camel, data_pdf, versao)
                caminho_arquivo = os.path.join(output_dir, nome_arquivo)
                if not os.path.exists(caminho_arquivo):
                    break
                versao += 1

            # Salva a imagem
            imagem_extraida.save(caminho_arquivo)
            print(f"✅ Imagem salva: {nome_arquivo}")

            doc.close()

        except Exception as e:
            print(f"⚠️ Erro ao processar {filename}: {e}")
