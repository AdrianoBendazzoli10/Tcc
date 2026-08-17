from analyzers.ocr_analyzer import OCRAnalyzer
from analyzers.document_comparator import DocumentComparator


ocr = OCRAnalyzer()

documento1 = ocr.analyze("oculista.jpeg")
documento2 = ocr.analyze("obito.jpg")


print("DOCUMENTO 1")
print("Sucesso:", documento1.success)

if documento1.success:
    print("Nome:", documento1.data["fields"]["nome"])
    print("CPF:", documento1.data["fields"]["cpf"])
else:
    print("Erro:", documento1.warnings)


print("\nDOCUMENTO 2")
print("Sucesso:", documento2.success)

if documento2.success:
    print("Nome:", documento2.data["fields"]["nome"])
    print("CPF:", documento2.data["fields"]["cpf"])
else:
    print("Erro:", documento2.warnings)


if documento1.success and documento2.success:

    comparador = DocumentComparator()

    resultado = comparador.compare(
        documento1,
        documento2
    )

    print("\n==============================")
    print("COMPARAÇÃO")
    print("==============================")

    print(
        "Nome:",
        resultado["campos"]["nome"]
    )

    print(
        "CPF:",
        resultado["campos"]["cpf"]
    )

    print(
        "Data:",
        resultado["campos"]["data"]
    )

    print(
        "\nCompatibilidade:",
        resultado["compatibilidade"]
    )

    print(
        "Resultado:",
        resultado["status"]
    )