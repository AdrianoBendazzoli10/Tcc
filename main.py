from analyzers.metadata_analyzer import MetadataAnalyzer


arquivo = "receita oculista 3 prescricoes.jpeg"

analyzer = MetadataAnalyzer()

resultado = analyzer.analyze(arquivo)

print(resultado)
