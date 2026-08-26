from analyzers.ocr_analyzer import OCRAnalyzer
from analyzers.metadata_analyzer import MetadataAnalyzer


def analisar_documento(caminho_arquivo):
    """
    Executa os analisadores disponíveis no documento.
    """

    resultados = {}

    # Análise de OCR
    try:
        ocr_analyzer = OCRAnalyzer()
        resultados["ocr"] = ocr_analyzer.analyze(caminho_arquivo)
    except Exception as erro:
        resultados["ocr"] = {
            "sucesso": False,
            "erro": str(erro)
        }

    # Análise de metadados
    try:
        metadata_analyzer = MetadataAnalyzer()
        resultados["metadata"] = metadata_analyzer.analyze(caminho_arquivo)
    except Exception as erro:
        resultados["metadata"] = {
            "sucesso": False,
            "erro": str(erro)
        }

    return resultados


def exibir_resultados(resultados):
    """
    Exibe os resultados das análises no terminal.
    """

    print("\n" + "=" * 50)
    print("        ANÁLISE DO DOCUMENTO")
    print("=" * 50)

    for nome_analisador, resultado in resultados.items():

        print(f"\n[{nome_analisador.upper()}]")

        if resultado is None:
            print("Nenhum resultado encontrado.")
            continue

        print(resultado)

    print("\n" + "=" * 50)


def main():
    """
    Função principal do sistema.
    """

    caminho_arquivo = input(
        "Digite o caminho do documento: "
    ).strip()

    if not caminho_arquivo:
        print("Nenhum arquivo informado.")
        return

    print("\nIniciando análise...")

    resultados = analisar_documento(caminho_arquivo)

    exibir_resultados(resultados)


if __name__ == "__main__":
    main()