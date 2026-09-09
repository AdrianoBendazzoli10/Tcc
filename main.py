from analyzers.ocr_analyzer import OCRAnalyzer
from analyzers.metadata_analyzer import MetadataAnalyzer


SEVERIDADES = {
    "high": "ALTA",
    "medium": "MÉDIA",
    "low": "BAIXA",
}

STATUS_CPF = {
    "valid": "Válido",
    "corrected": "Corrigido automaticamente",
    "ambiguous": "Leitura ambígua",
    "invalid": "Inválido",
    "not_found": "Não encontrado",
}


def _valor_ou_indisponivel(valor):
    return valor if valor not in (None, "", []) else "Não identificado"


def _exibir_alertas(resultado):
    if not resultado.evidences:
        print("  Alertas: nenhum")
        return

    print(f"  Alertas encontrados: {len(resultado.evidences)}")
    for evidencia in resultado.evidences:
        severidade = SEVERIDADES.get(evidencia.severity, evidencia.severity.upper())
        print(f"    - [{severidade}] {evidencia.message}")


def _exibir_ocr(resultado):
    campos = resultado.data.get("fields", {})
    datas = campos.get("datas", [])

    print(f"  Status: {'Concluído' if resultado.success else 'Falhou'}")
    print(f"  Nome: {_valor_ou_indisponivel(campos.get('nome'))}")
    print(f"  CPF: {_valor_ou_indisponivel(campos.get('cpf'))}")
    print(f"  Situação do CPF: {STATUS_CPF.get(campos.get('cpf_status'), 'Não identificada')}")
    print(f"  Datas: {', '.join(datas) if datas else 'Não identificadas'}")
    print(f"  Confiança do OCR: {resultado.data.get('confidence', 0):.2f}%")
    print(f"  Pontuação de alertas: {resultado.score} (quanto maior, mais atenção necessária)")
    print(f"  Tempo de análise: {resultado.execution_time:.2f}s")
    _exibir_alertas(resultado)


def _exibir_metadata(resultado):
    dados = resultado.data
    dimensoes = "Não disponíveis"
    if dados.get("width") and dados.get("height"):
        dimensoes = f"{dados['width']} x {dados['height']} px"

    print(f"  Status: {'Concluído' if resultado.success else 'Falhou'}")
    print(f"  Formato: {_valor_ou_indisponivel(dados.get('format'))}")
    print(f"  Dimensões: {dimensoes}")
    print(f"  Modo de cor: {_valor_ou_indisponivel(dados.get('mode'))}")
    print(f"  Metadados EXIF: {'Encontrados' if dados.get('exif') else 'Não encontrados'}")
    print(f"  Pontuação de alertas: {resultado.score} (quanto maior, mais atenção necessária)")
    print(f"  Tempo de análise: {resultado.execution_time:.2f}s")
    _exibir_alertas(resultado)


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

    print("\n" + "=" * 64)
    print("                    RESULTADO DA ANÁLISE")
    print("=" * 64)

    for nome_analisador, resultado in resultados.items():

        titulos = {
            "ocr": "LEITURA DO DOCUMENTO (OCR)",
            "metadata": "METADADOS DO ARQUIVO",
        }
        print(f"\n--- {titulos.get(nome_analisador, nome_analisador.upper())} ---")

        if resultado is None:
            print("Nenhum resultado encontrado.")
            continue

        if isinstance(resultado, dict):
            print(f"  Falha: {resultado.get('erro', 'Erro desconhecido')}")
        elif nome_analisador == "ocr":
            _exibir_ocr(resultado)
        elif nome_analisador == "metadata":
            _exibir_metadata(resultado)
        else:
            print(resultado)

    print("\n" + "=" * 64)


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
