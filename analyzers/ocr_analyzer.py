import os
import re
import io
import time

import fitz  # PyMuPDF
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

from PIL import Image

from core.analysis_result import AnalysisResult
from core.evidence import Evidence


class OCRAnalyzer:

    # Padrões usados para extrair campos do texto reconhecido pelo OCR
    # CPF com ou sem pontuação (ex: 470.764.086-91 ou 47076408691)
    CPF_PATTERN = re.compile(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}")
    DATE_PATTERN = re.compile(r"\d{2}/\d{2}/\d{4}")
    # "Nome:" seguido de palavras em maiúsculas ou capitalizadas, na mesma linha.
    # Usa espaço literal (não \s) para não atravessar quebras de linha, e limita
    # explicitamente a maiúsculas (mesmo com IGNORECASE) para não misturar "Nome Social" etc.
    NAME_PATTERN = re.compile(
        r"(?i:nome)[:\s]+([A-ZÀ-Ú]+(?: [A-ZÀ-Ú]+)+)",
    )

    # Abaixo desse valor (0-100), consideramos o texto pouco confiável
    MIN_CONFIDENCE = 60


    def analyze(self, file_path):

        start = time.time()

        try:

            extension = os.path.splitext(file_path)[1].lower()


            if extension == ".pdf":

                data, evidences = self._analyze_pdf(file_path)


            elif extension in [".jpg", ".jpeg", ".png"]:

                data, evidences = self._analyze_image(file_path)


            else:

                return AnalysisResult(
                    success=False,
                    module="ocr",
                    warnings=[
                        "Formato de arquivo não suportado."
                    ]
                )


            score = sum(evidence.weight for evidence in evidences)


            return AnalysisResult(

                success=True,

                module="ocr",

                score=score,

                data=data,

                evidences=evidences,

                execution_time=time.time() - start

            )


        except Exception as e:

            return AnalysisResult(

                success=False,

                module="ocr",

                warnings=[
                    str(e)
                ]

            )


    # ---------- PDF ----------

    def _analyze_pdf(self, file_path):

        pdf = fitz.open(file_path)

        full_text = ""
        confidences = []

        for page in pdf:

            # renderiza a página em resolução maior para melhorar a leitura do OCR
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            image = Image.open(io.BytesIO(pix.tobytes("png")))

            text, page_confidences = self._ocr_image(image)

            full_text += text + "\n"
            confidences.extend(page_confidences)

        fields = self._extract_fields(full_text)
        avg_confidence = self._average_confidence(confidences)

        evidences = self._build_evidences(full_text, fields, avg_confidence)

        return {

            "type": "PDF",
            "pages": len(pdf),
            "text": full_text.strip(),
            "fields": fields,
            "confidence": avg_confidence

        }, evidences


    # ---------- IMAGEM ----------

    def _analyze_image(self, file_path):

        image = Image.open(file_path)

        text, confidences = self._ocr_image(image)

        fields = self._extract_fields(text)
        avg_confidence = self._average_confidence(confidences)

        evidences = self._build_evidences(text, fields, avg_confidence)

        return {

            "type": "IMAGE",
            "text": text.strip(),
            "fields": fields,
            "confidence": avg_confidence

        }, evidences


    # ---------- OCR ----------

    def _ocr_image(self, image):

        # texto puro reconhecido
        text = pytesseract.image_to_string(image, lang="por")

        # dados detalhados, incluindo confiança por palavra reconhecida
        details = pytesseract.image_to_data(
            image, lang="por", output_type=pytesseract.Output.DICT
        )

        confidences = [
            int(c) for c in details.get("conf", [])
            if str(c).lstrip("-").isdigit() and int(c) >= 0
        ]

        return text, confidences


    def _average_confidence(self, confidences):

        if not confidences:
            return 0.0

        return round(sum(confidences) / len(confidences), 2)


    # ---------- EXTRAÇÃO DE CAMPOS ----------

    def _extract_fields(self, text):

        cpf_match = self.CPF_PATTERN.search(text)
        date_matches = self.DATE_PATTERN.findall(text)
        name_match = self.NAME_PATTERN.search(text)

        return {

            "nome": name_match.group(1).strip() if name_match else None,
            "cpf": cpf_match.group(0) if cpf_match else None,
            "datas": date_matches

        }


    # ---------- EVIDÊNCIAS ----------

    def _build_evidences(self, text, fields, avg_confidence):

        evidences = []


        if not text.strip():

            evidences.append(

                Evidence(
                    code="OCR_NO_TEXT",
                    message="Não foi possível extrair texto do documento.",
                    severity="high",
                    weight=25
                )

            )

            # se não há texto nenhum, não faz sentido checar os campos
            return evidences


        if avg_confidence and avg_confidence < self.MIN_CONFIDENCE:

            evidences.append(

                Evidence(
                    code="OCR_LOW_CONFIDENCE",
                    message=f"Confiança média do OCR baixa ({avg_confidence}%), "
                            f"o texto extraído pode estar incorreto.",
                    severity="medium",
                    weight=10
                )

            )


        if not fields["nome"]:

            evidences.append(

                Evidence(
                    code="OCR_NAME_NOT_FOUND",
                    message="Não foi possível identificar um nome no documento.",
                    severity="low",
                    weight=5
                )

            )


        if not fields["cpf"]:

            evidences.append(

                Evidence(
                    code="OCR_CPF_NOT_FOUND",
                    message="Não foi possível identificar um CPF no documento.",
                    severity="low",
                    weight=5
                )

            )


        if not fields["datas"]:

            evidences.append(

                Evidence(
                    code="OCR_DATE_NOT_FOUND",
                    message="Não foi possível identificar nenhuma data no documento.",
                    severity="low",
                    weight=5
                )

            )


        return evidences
