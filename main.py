from analyzers.ocr_analyzer import OCRAnalyzer
from analyzers.metadata_analyzer import MetadataAnalyzer
from analyzers.document_comparator import DocumentComparator


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

STATUS_COMPARACAO = {
    "COMPATIVEL": "Compatível",
    "DIVERGENTE": "Divergente",
    "NAO_IDENTIFICADO": "Não foi possível comparar",
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


def exibir_resultados(resultados, titulo="RESULTADO DA ANÁLISE"):
    """
    Exibe os resultados das análises no terminal.
    """

    print("\n" + "=" * 64)
    print(f"{titulo:^64}")
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


def exibir_comparacao(comparacao):
    """Exibe a conclusão da comparação entre os dois documentos."""
    status = comparacao["status"].replace("_", " ").title()
    compatibilidade = comparacao.get("compatibilidade")

    print("\n" + "=" * 64)
    print(f"{'COMPARAÇÃO ENTRE OS DOCUMENTOS':^64}")
    print("=" * 64)

    for campo, resultado in comparacao["campos"].items():
        nome_campo = {"nome": "Nome", "cpf": "CPF", "data": "Datas"}[campo]
        descricao = STATUS_COMPARACAO.get(resultado, resultado)
        print(f"  {nome_campo}: {descricao}")

    if compatibilidade is None:
        print("  Compatibilidade: não calculada")
    else:
        print(f"  Compatibilidade: {compatibilidade:.2f}%")

    print(f"  Resultado final: {status}")

    if comparacao["status"] == "COMPATIVEL":
        print("  Conclusão: os dados comparáveis são compatíveis.")
    elif comparacao["status"] == "INCONSISTENTE":
        print("  Conclusão: existem divergências que exigem revisão humana.")
    else:
        print("  Conclusão: não há dados suficientes para uma conclusão.")

    print("=" * 64)


def main():
    """
    Função principal do sistema.
    """

    caminho_documento1 = input(
        "Digite o caminho do documento 1: "
    ).strip()

    caminho_documento2 = input(
        "Digite o caminho do documento 2: "
    ).strip()

    if not caminho_documento1 or not caminho_documento2:
        print("É necessário informar os dois documentos.")
        return

    print("\nAnalisando o documento 1...")
    resultados1 = analisar_documento(caminho_documento1)

    print("Analisando o documento 2...")
    resultados2 = analisar_documento(caminho_documento2)

    exibir_resultados(resultados1, "DOCUMENTO 1")
    exibir_resultados(resultados2, "DOCUMENTO 2")

    ocr1 = resultados1.get("ocr")
    ocr2 = resultados2.get("ocr")

    if isinstance(ocr1, dict) or isinstance(ocr2, dict) or not ocr1.success or not ocr2.success:
        print("Não foi possível comparar: a análise de um dos documentos falhou.")
        return

    comparacao = DocumentComparator().compare(ocr1, ocr2)
    exibir_comparacao(comparacao)


if __name__ == "__main__":
    main()
