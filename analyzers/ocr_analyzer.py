import os
import re
import io
import time
import shutil
import platform

import fitz  # PyMuPDF
import pytesseract

from PIL import Image


def _configurar_tesseract():
    """
    Descobre o executável do Tesseract sem depender de um caminho fixo
    de Windows. Ordem de prioridade:

      1. Variável de ambiente TESSERACT_CMD, se o usuário quiser forçar
         um caminho específico (ex: instalação não padrão).
      2. `tesseract` já no PATH do sistema (funciona out-of-the-box em
         Linux/Mac quando instalado via apt/brew).
      3. Caminhos padrão conhecidos de instalação no Windows, como
         fallback só quando os anteriores falharem.

    Se nada for encontrado, deixa o pytesseract com o comportamento
    padrão (ele mesmo vai lançar um erro claro na hora do uso, em vez
    de travar silenciosamente aqui na importação do módulo).
    """

    caminho_env = os.environ.get("TESSERACT_CMD")
    if caminho_env and os.path.isfile(caminho_env):
        pytesseract.pytesseract.tesseract_cmd = caminho_env
        return

    caminho_path = shutil.which("tesseract")
    if caminho_path:
        pytesseract.pytesseract.tesseract_cmd = caminho_path
        return

    if platform.system() == "Windows":
        candidatos_windows = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        for candidato in candidatos_windows:
            if os.path.isfile(candidato):
                pytesseract.pytesseract.tesseract_cmd = candidato
                return


_configurar_tesseract()

from core.analysis_result import AnalysisResult
from core.evidence import Evidence
from core.cpf_validator import find_cpf


class OCRAnalyzer:

    # Padrão usado para extrair a data do texto reconhecido pelo OCR.
    # O CPF não usa mais regex simples aqui: a extração, validação de
    # dígito verificador e correção de erros de OCR ficam a cargo de
    # core.cpf_validator.find_cpf(), que é bem mais robusto.
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

        cpf_result = find_cpf(text)
        date_matches = self.DATE_PATTERN.findall(text)
        name_match = self.NAME_PATTERN.search(text)

        # "cpf" continua sendo o campo simples (string de dígitos ou None),
        # para não quebrar quem já consome fields["cpf"] (ex: DocumentComparator).
        # Em caso de status "ambiguous", deixamos None de propósito: não dá
        # pra afirmar qual dos candidatos é o correto sem revisão humana.
        if cpf_result.status in ("valid", "corrected", "invalid"):
            cpf_valor = cpf_result.value or (
                cpf_result.candidates[0] if cpf_result.candidates else None
            )
        else:
            cpf_valor = None

        return {

            "nome": name_match.group(1).strip() if name_match else None,
            "cpf": cpf_valor,
            "cpf_status": cpf_result.status,
            "cpf_candidates": cpf_result.candidates,
            "cpf_raw_ocr": cpf_result.raw_ocr_text,
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


        cpf_status = fields.get("cpf_status")

        if cpf_status == "not_found":

            evidences.append(

                Evidence(
                    code="OCR_CPF_NOT_FOUND",
                    message="Não foi possível identificar um CPF no documento.",
                    severity="low",
                    weight=5
                )

            )

        elif cpf_status == "corrected":

            # O OCR provavelmente errou a leitura (10 ou 12 dígitos), mas
            # havia só UM candidato que resultava em CPF matematicamente
            # válido, então a correção automática é razoavelmente segura.
            # Ainda assim registramos como evidência informativa, para
            # rastreabilidade no relatório final.
            evidences.append(

                Evidence(
                    code="OCR_CPF_CORRECTED",
                    message=f"CPF corrigido automaticamente a partir de leitura "
                            f"de OCR inconsistente (texto bruto: "
                            f"{fields.get('cpf_raw_ocr')!r}).",
                    severity="low",
                    weight=5
                )

            )

        elif cpf_status == "ambiguous":

            # Mais de um candidato de CPF resultou em checksum válido:
            # não dá pra confirmar automaticamente qual é o correto.
            evidences.append(

                Evidence(
                    code="OCR_CPF_AMBIGUOUS",
                    message=f"Leitura do CPF ambígua, requer revisão manual. "
                            f"Candidatos válidos: {fields.get('cpf_candidates')}.",
                    severity="medium",
                    weight=15
                )

            )

        elif cpf_status == "invalid":

            # 11 dígitos, formatação correta, mas o dígito verificador
            # NÃO bate. Diferente dos casos acima, aqui não é um provável
            # erro de OCR (o formato já veio "redondo") — é um indício de
            # que o dado no próprio documento é inconsistente, o que pode
            # apontar para adulteração.
            evidences.append(

                Evidence(
                    code="CPF_CHECKSUM_INVALID",
                    message=f"CPF com formatação válida, mas dígito verificador "
                            f"incorreto ({fields.get('cpf')}). Pode indicar "
                            f"documento adulterado ou erro de preenchimento.",
                    severity="high",
                    weight=25
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
