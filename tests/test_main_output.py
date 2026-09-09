from core.analysis_result import AnalysisResult
from core.evidence import Evidence
from main import exibir_comparacao, exibir_resultados


def test_exibe_resumo_claro_do_ocr(capsys):
    resultado = AnalysisResult(
        success=True,
        module="ocr",
        score=25,
        data={
            "fields": {
                "nome": "RICARDO CAVALCANTE DE ALBUQUERQUE",
                "cpf": "34211988504",
                "cpf_status": "invalid",
                "datas": ["22/05/2024"],
            },
            "confidence": 94.62,
        },
        evidences=[
            Evidence("CPF_CHECKSUM_INVALID", "CPF inválido.", "high", 25)
        ],
        execution_time=16.05,
    )

    exibir_resultados({"ocr": resultado})
    saida = capsys.readouterr().out

    assert "RICARDO CAVALCANTE DE ALBUQUERQUE" in saida
    assert "Situação do CPF: Inválido" in saida
    assert "Datas: 22/05/2024" in saida
    assert "Confiança do OCR: 94.62%" in saida
    assert "[ALTA] CPF inválido." in saida


def test_exibe_comparacao_entre_documentos(capsys):
    exibir_comparacao({
        "status": "INCONSISTENTE",
        "campos": {
            "nome": "COMPATIVEL",
            "cpf": "DIVERGENTE",
            "data": "NAO_IDENTIFICADO",
        },
        "compatibilidade": 44.44,
    })
    saida = capsys.readouterr().out

    assert "Nome: Compatível" in saida
    assert "CPF: Divergente" in saida
    assert "Datas: Não foi possível comparar" in saida
    assert "Compatibilidade: 44.44%" in saida
    assert "Resultado final: Inconsistente" in saida


def test_exibe_metadados_especificos_de_pdf(capsys):
    resultado = AnalysisResult(
        success=True,
        module="metadata",
        data={
            "type": "PDF",
            "pages": 2,
            "creator": "Canva",
            "producer": "PDF Engine",
            "creation_date": "D:20260909",
            "modification_date": None,
            "encrypted": False,
        },
    )

    exibir_resultados({"metadata": resultado})
    saida = capsys.readouterr().out

    assert "Formato: PDF" in saida
    assert "Páginas: 2" in saida
    assert "Criador: Canva" in saida
    assert "Criptografado: Não" in saida
    assert "Metadados EXIF" not in saida
