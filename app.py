import streamlit as st
import fitz  # PyMuPDF
import re
import os
import hashlib
from datetime import datetime
from PIL import Image
import tempfile

# Configuração da página
st.set_page_config(page_title="Extrator de Fotos de PDFs", layout="centered")
st.title("📄➡️🖼️ Extrator de Fotos de PDFs")

# Função para gerar hash da imagem
def gerar_hash_imagem(pixmap):
    img_bytes = pixmap.tobytes("ppm")
    return hashlib.md5(img_bytes).hexdigest()

# Função para gerar o nome do arquivo com versão
def gerar_nome_arquivo(matricula, nome_camel, data_pdf, versao, imagem_index):
    return f"{matricula}_{nome_camel}_{data_pdf}_img{imagem_index}_v{versao}.jpeg"

# Upload de múltiplos arquivos
uploaded_files = st.file_uploader("📤 Envie um ou mais arquivos PDF", type="pdf", accept_multiple_files=True)

if uploaded_files:
    processar = st.button("🔍 Iniciar Extração de Imagens")

    if processar:
        st.info("Processando PDFs...")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = os.path.join(temp_dir, "fotos_funcionarios")
            os.makedirs(output_dir, exist_ok=True)

            total_extraidas = 0

            for uploaded_file in uploaded_files:
                filename = uploaded_file.name
                pdf_path = os.path.join(temp_dir, filename)

                with open(pdf_path, "wb") as f:
                    f.write(uploaded_file.read())

                st.write(f"📄 Processando: `{filename}`")

                try:
                    doc = fitz.open(pdf_path)

                    # Extrai texto
                    full_text = ""
                    for page in doc:
                        full_text += page.get_text()

                    match = re.search(r'(\d{4,6})\s+([A-Z\s]{5,})', full_text)
                    if not match:
                        st.warning(f"⚠️ Matrícula e nome não encontrados em {filename}")
                        continue

                    matricula = match.group(1)
                    nome_raw = match.group(2).strip()
                    nome_camel = "_".join(word.capitalize() for word in nome_raw.split())

                    # Usa data de modificação
                    mod_timestamp = os.path.getmtime(pdf_path)
                    data_pdf = datetime.fromtimestamp(mod_timestamp).strftime("%Y%m%d_%H%M%S")

                    imagem_index = 0

                    for page_index, page in enumerate(doc):
                        images = page.get_images(full=True)
                        for img in images:
                            xref = img[0]
                            pix = fitz.Pixmap(doc, xref)
                            if pix.n >= 5:
                                pix = fitz.Pixmap(fitz.csRGB, pix)

                            imagem_hash = gerar_hash_imagem(pix)

                            # Verifica se hash já existe
                            hash_ja_existente = False
                            for img_file in os.listdir(output_dir):
                                if img_file.lower().endswith(".jpeg"):
                                    with open(os.path.join(output_dir, img_file), "rb") as f:
                                        if hashlib.md5(f.read()).hexdigest() == imagem_hash:
                                            hash_ja_existente = True
                                            break
                            if hash_ja_existente:
                                st.warning(f"⏭️ Imagem duplicada ignorada em {filename} (página {page_index+1})")
                                continue

                            # Nome de arquivo
                            versao = 1
                            while True:
                                nome_arquivo = gerar_nome_arquivo(matricula, nome_camel, data_pdf, versao, imagem_index)
                                caminho_arquivo = os.path.join(output_dir, nome_arquivo)
                                if not os.path.exists(caminho_arquivo):
                                    break
                                versao += 1

                            # Redimensiona
                            imagem_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                            imagem_redimensionada = imagem_pil.resize((820, 1165), Image.LANCZOS)
                            imagem_redimensionada.save(caminho_arquivo, "JPEG", quality=95)

                            total_extraidas += 1
                            imagem_index += 1

                            st.success(f"✅ Salvo: `{nome_arquivo}`")
                            st.image(caminho_arquivo, width=250)

                    doc.close()

                except Exception as e:
                    st.error(f"Erro ao processar {filename}: {e}")

            st.success(f"🎉 Extração concluída: {total_extraidas} imagens salvas.")

            # Download zip
            import zipfile
            from io import BytesIO

            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for img_file in os.listdir(output_dir):
                    zipf.write(os.path.join(output_dir, img_file), arcname=img_file)

            zip_buffer.seek(0)
            st.download_button(
                label="📦 Baixar todas as imagens (.zip)",
                data=zip_buffer,
                file_name="fotos_funcionarios.zip",
                mime="application/zip"
            )
