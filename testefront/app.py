from flask import Flask, render_template, request
from analyzers.ocr_analyzer import OCRAnalyzer
from analyzers.document_comparator import DocumentComparator

import os
import tempfile


app = Flask(__name__)

ocr = OCRAnalyzer()
comparador = DocumentComparator()


@app.route("/", methods=["GET", "POST"])
def index():

    resultado = None
    erro = None

    if request.method == "POST":

        arquivo1 = request.files.get("documento1")
        arquivo2 = request.files.get("documento2")

        if not arquivo1 or not arquivo2:
            erro = "Selecione os dois documentos."

        else:

            caminho1 = None
            caminho2 = None

            try:

                extensao1 = os.path.splitext(
                    arquivo1.filename
                )[1]

                extensao2 = os.path.splitext(
                    arquivo2.filename
                )[1]

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=extensao1
                ) as temp1:

                    arquivo1.save(temp1.name)
                    caminho1 = temp1.name

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=extensao2
                ) as temp2:

                    arquivo2.save(temp2.name)
                    caminho2 = temp2.name

                documento1 = ocr.analyze(caminho1)
                documento2 = ocr.analyze(caminho2)

                if not documento1.success:

                    erro = (
                        "Erro no documento 1: "
                        + str(documento1.warnings)
                    )

                elif not documento2.success:

                    erro = (
                        "Erro no documento 2: "
                        + str(documento2.warnings)
                    )

                else:

                    comparacao = comparador.compare(
                        documento1,
                        documento2
                    )

                    resultado = {
                        "documento1": documento1.data,
                        "documento2": documento2.data,
                        "comparacao": comparacao
                    }

            except Exception as e:

                erro = str(e)

            finally:

                if caminho1 and os.path.exists(caminho1):
                    os.remove(caminho1)

                if caminho2 and os.path.exists(caminho2):
                    os.remove(caminho2)

    return render_template(
        "index.html",
        resultado=resultado,
        erro=erro
    )


if __name__ == "__main__":
    app.run(debug=True)