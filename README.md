
O VALID é uma plataforma inteligente de análise e validação documental que utiliza Inteligência Artificial, OCR e técnicas de visão computacional para extrair informações, verificar a integridade de documentos, analisar metadados, detectar possíveis indícios de adulteração e gerar relatórios explicáveis com base em evidências.

projeto desenvolvido em grupo, com auxílio do ChatGPT  e do Claude

esse sistema tem como principal objetivo auxiliar profissionais que lidam com uma alta demanda de documentos diariamente, fornecendo uma análise automatizada de diferentes características dos arquivos para identificar possíveis inconsistências e indícios de adulteração.

o Validador de Documentos funciona como uma ferramenta de apoio à análise, contribuindo para tornar o processo de verificação mais rápido e eficiente. Entretanto, os resultados apresentados pelo sistema não garantem, por si só, a autenticidade ou falsidade de um documento, sendo necessária a análise humana para uma decisão definitiva.

Desenvolvimento:

11/06 - primeiras pesquisas sobre metadados e como eu poderia usa-lo para resolver nosso problema, descobri que as fotos guardam os metadadods EXIF e poderiamos usar eles para descobrir se um arquivo passou por photoshop, canva e etc....
Não consegui fazer nada quanto a arquivos gerados por IA pois eles não guardam esses metadados.


09/07 - começo da estruturação dessa parte, fiz tudo com apenas um arquivo, "analyzer.py".
Ele foi dividido em 4 partes, a primeira é a detecção dos metadados exif, que procura informações "escondidas" das imagens, a data original, o software ultilizado, a câmera ultilizada, a data de modificação e se há algum indício de Photoshop.


16/07 - na segunda parte foi implementado o ELA (Error Level Analysis), que após ser programado pega a imagem original, salve ela novamente em JPEG com a qualidade de 75%, compara a imagem original com a comprimida e calcula onde existem diferenças muito grandes (Pode ser um sinal de adulteração)..

basicamente eu criei dois resultados, os alertas (que vão guardar as suspeitas detectadas) e os dados (que vão guardar os valores calculados pelo ELA)

após o envio da imagem, o sistema recompacta a imagem para uma qualidsade inferior (75%) e depois ele abre essa nova imagem... a ideia é que uma imagem que já foi comprimida anteriormente pode apresentar um determinado padrão de erro quando é comprimida novamente

Depois ela tranforma a imagem em numeros (uma imagem para o computador é basicamente uma enorme matriz de números) e calcula a diferença entre elas comparando pixel por pixel.

após isso ele pega todas as diferenças dos pixels e calcula a média, quando um pixel tem uma diferença muito maior do que a média o sistema gera um alerta e um score de confiabilidade.


23/07 - na terceira parte foi iplementado um modelo de dnn, usado para detectar rostos.

essa parte é bem simples, o verificador procura quantos rostos exitem em um documento e se encontrar mais do que um ele gera um alerta.

já na quarta parte foi usado a biblioteca pymupdf, que transforma um pdf em imagem para o dnn poder fazer a verificação.


05/08 - foi iniciado a etruturação da parte de ocr, usada para ler o conteúdo do documento, o usuário coloca dois sou mais documentos de alguma pessoa para verificar se o nome, cpf e data são compatíveis uns com os outros.

Link Tesseract - https://github.com/UB-Mannheim/tesseract/wiki?
