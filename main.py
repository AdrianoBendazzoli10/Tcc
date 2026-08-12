from analyzers.ocr_analyzer import OCRAnalyzer

arquivo = "receita oculista 3 prescricoes.jpeg"

analyzer = OCRAnalyzer()
resultado = analyzer.analyze(arquivo)
print(resultado)