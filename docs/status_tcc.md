# Status do Projeto — Verificador de Documentos (TCC)

Repositório: [github.com/AdrianoBendazzoli10/Tcc](https://github.com/AdrianoBendazzoli10/Tcc)

---

## 1. Objetivo

Construir um sistema que analisa dois documentos (imagem ou PDF), extrai
campos de identificação (nome, CPF, data) via OCR, e **compara os dois
documentos entre si** para identificar inconsistências que podem indicar
adulteração ou fraude de identidade — por exemplo, dois documentos com o
mesmo CPF mas nomes de pessoas diferentes.

O sistema não tenta provar adulteração de forma definitiva: ele gera um
**score de compatibilidade** e uma lista de **evidências** (alertas com
peso e severidade), deixando a decisão final para revisão humana.

---

## 2. Arquitetura atual

```
Tcc/
├── main.py                          # script de teste simples (roda 2 documentos fixos)
├── requirements.txt
├── core/
│   ├── analysis_result.py           # dataclass: resultado padrão de qualquer analisador
│   ├── evidence.py                  # dataclass: um alerta (código, mensagem, severidade, peso)
│   └── cpf_validator.py             # valida/corrige CPF a partir de TEXTO
├── analyzers/
│   ├── ocr_analyzer.py              # OCR (Tesseract) + extração de campos + evidências
│   ├── cpf_from_image.py            # extrai CPF isolando a região da IMAGEM (bounding box)
│   ├── document_comparator.py       # compara dois AnalysisResult entre si
│   └── metadata_analyzer.py         # lê metadados EXIF/PDF (existe, pouco explorado até agora)
└── testefront/
    ├── app.py                       # interface web Flask (upload de 2 arquivos)
    ├── static/style.css
    └── templates/index.html

```

**Fluxo de dados:** `main.py` (ou `testefront/app.py`) → `OCRAnalyzer.analyze()`
roda em cada documento → `DocumentComparator.compare()` cruza os dois
resultados → score de 0 a 100 + status (`COMPATIVEL` / `INCONSISTENTE`).

---

## 3. O que já está implementado e testado

### 3.1 Validação e correção de CPF (`core/cpf_validator.py`)

- Valida o dígito verificador oficial (módulo 11), não só o formato.
- Corrige erros de OCR (10 ou 12 dígitos em vez de 11) usando a posição dos separadores (`.`/`-`) quando disponíveis, com fallback para testar inserção/remoção em cada posição.
- Retorna sempre um status explícito: `valid`, `corrected`, `ambiguous`, `invalid`, `not_found` — nunca um valor "chutado" silenciosamente.

### 3.2 Extração de CPF por região da imagem (`analyzers/cpf_from_image.py`)

- Localiza a palavra "CPF" via `pytesseract.image_to_data` (que dá a posição de cada palavra reconhecida).
- Usa as próprias palavras da mesma linha (não uma largura de recorte fixa) para isolar só o valor do CPF, evitando grudar em campos vizinhos (ex: `RG:` colado ao lado).
- Reprocessa a região isolada com whitelist de dígitos, o que resolve erros de OCR **na origem**, sem precisar de correção estatística depois.
- Integrado como fallback automático no `OCRAnalyzer`: só é acionado quando a leitura de página inteira dá `ambiguous` ou `not_found` — não quando dá `invalid` (11 dígitos bem formatados, checksum errado), para não mascarar um possível indício real de adulteração.

### 3.3 Correção de orientação EXIF (`analyzers/ocr_analyzer.py`)

- Fotos tiradas com celular têm uma tag EXIF de orientação que os visualizadores aplicam automaticamente, mas o `PIL.Image.open()` não aplica sozinho. Sem correção, o Tesseract lê a imagem "deitada" e produz texto embaralhado. Corrigido com `ImageOps.exif_transpose()`.

### 3.4 Extração de nome mais robusta

- `NAME_PATTERN` aceita nome em CAIXA ALTA (`RICARDO CAVALCANTE...`) e em Title Case (`Ana Souza`), com tolerância a rótulos bilíngues em linha separada (`Nome / Name` seguido do valor na linha seguinte).
- Heurística de fallback (`_extract_name_heuristic`) para documentos **sem rótulo** "Nome:" explícito (ex: carteirinhas/crachás que só listam o nome direto): procura a linha mais "parecida com nome" (2-6 palavras, todas iniciando com maiúscula, não sendo termos institucionais conhecidos). Marca a origem do valor (`nome_fonte: "rotulo"` ou `"heuristica"`) para rastreabilidade.

### 3.5 Comparação de nome por similaridade (`analyzers/document_comparator.py`)

- Antes: comparação exata (`nome1 == nome2`) — qualquer diferença mínima (ex: sobrenome cortado por quebra de linha no OCR) já dava `DIVERGENTE`.
- Agora: similaridade de tokens (Jaccard), ignorando conectivos comuns (`DE`, `DA`, `DO`...). Introduz status `PARCIALMENTE_COMPATIVEL` quando a similaridade é alta mas não total, com **crédito proporcional** no cálculo do score (não tudo-ou-nada).
- Nomes genuinamente diferentes (ex: fraude real, "Maria Joana" vs "Ana Souza") continuam corretamente `DIVERGENTE`, com similaridade \~0.

### 3.6 Correções de ambiente/infraestrutura

- Caminho do Tesseract não depende mais de path fixo do Windows (detecção automática: env var → PATH do sistema → fallback Windows).
- Bug de import corrigido no `testefront/`: rodar `python testefront/app.py` direto quebra porque o Python usa a pasta do script como referência. Solução adotada: `testefront/__init__.py` + rodar como `python -m testefront.app`.
- `testefront/app.py` agora passa as `evidences` de cada documento pro template (antes se perdiam, nunca apareciam na tela).
- `index.html`/`style.css` atualizados para mostrar o status real do CPF (ambíguo/corrigido/checksum inválido) e a lista de alertas por documento, com cores por severidade.

---

## 4. Achados de teste com documentos reais

| Documento Achado                                 |                                                                                                                                                                              |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `obito.jpg`                                      | CPF com 11 dígitos, formatação perfeita, **checksum inválido** → gera `CPF_CHECKSUM_INVALID` (severidade alta), indício de inconsistência real no documento, não erro de OCR |
| `oculista.jpeg`                                  | CPF lido com 10 dígitos pela leitura de página inteira (`ambiguous`) → resolvido automaticamente pela extração por região, que leu os 11 dígitos corretos                    |
| `carteirinhaetecdri.jpg` / `cartaoonibusdri.jpg` | Fotos de celular com rotação EXIF; sem rótulo "Nome:" explícito (heurística resolveu)                                                                                        |
| `document.png` / `document_editado.png`          | Par de teste: mesmo CPF, nomes diferentes (`Maria Joana` vs `Ana Souza`) → corretamente identificado como `INCONSISTENTE`, o cenário central que o TCC quer detectar         |

---

## 5. Problemas e limitações conhecidas (em aberto)

1. **`DATE_PATTERN`** **só reconhece** **`dd/mm/aaaa`** **contíguo.** Documentos que
   escrevem a data por extenso ou em campos separados (ex: "Dia: 22 /
   Mês: 05 / Ano: 2024", como no `obito.jpg`) não são capturados, mesmo
   a data estando presente no texto. Gera um `OCR_DATE_NOT_FOUND` que na
   verdade é enganoso (a data existe, só não nesse formato).
2. **Heurística de nome funciona linha por linha.** Se o nome quebra em
   duas linhas no documento (ex: sobrenome isolado, como no
   `cartaoonibusdri.jpg`), ela não junta as duas — pega só a linha com
   mais palavras. A comparação por similaridade (item 3.5) atenua o
   impacto disso na comparação final, mas a extração em si ainda perde
   parte do nome.
3. **Discrepância entre o README e o código.** O README menciona EXIF,
   ELA (Error Level Analysis) e detecção de rosto via DNN como já
   implementados; nenhum dos três existe no repositório atual (só existe
   uma versão simples de leitura de metadados em
   `metadata_analyzer.py`, sem ELA nem detecção de rosto). Precisa
   alinhamento com o grupo: ou esse código existe em outro lugar e não
   foi commitado, ou o README está descrevendo algo que nunca chegou a
   ser implementado.
4. **`metadata_analyzer.py`** **pouco explorado.** Existe no repositório mas
   não foi testado a fundo nesta rodada de trabalho — não sabemos se
   está funcionando corretamente com os documentos reais que usamos.
5. **Limiar de similaridade de nome (****`LIMIAR_NOME_PARCIAL = 0.5`****) foi
   escolhido por raciocínio, não calibrado com dados.** Vale testar com
   mais pares de documentos (tanto casos de corte de OCR legítimo quanto
   tentativas de fraude) para confirmar se 0.5 é o ponto de corte certo.
6. **Sem testes automatizados.** Todas as correções até agora foram
   validadas manualmente, rodando contra os documentos de exemplo. Não
   há uma suíte de testes (`pytest` ou similar) que rode automaticamente
   e evite regressão quando alguém mexer no código de novo.

---

## 6. Próximos passos sugeridos (em ordem de prioridade)

1. **Alinhar com o grupo sobre ELA e detecção de rosto** (item 5.3) — decidir se será implementado, e ajustar o README para refletir a realidade do código antes da entrega.
2. **Melhorar** **`DATE_PATTERN`** para reconhecer mais formatos de data (por extenso, campos separados Dia/Mês/Ano).
3. **Revisar** **`metadata_analyzer.py`** com os mesmos documentos de teste já usados, pra garantir que está gerando evidências corretas.
4. **Calibrar o limiar de similaridade de nome** com mais pares de documentos reais (idealmente incluindo casos de fraude conhecidos e casos de erro de OCR legítimo).
5. **Escrever testes automatizados** (`pytest`) cobrindo pelo menos: validação de CPF, extração de campos, e comparação de documentos — para não regredir o que já foi corrigido.
6. **Juntar heurística de nome multi-linha** (opcional, trade-off: aumenta complexidade e risco de falso positivo).
7. **Documentar as decisões de design no texto do TCC**, especialmente: por que CPF com checksum inválido não passa por correção automática (para não mascarar adulteração), e por que a comparação de nome usa similaridade em vez de igualdade exata.

---

*Documento gerado a partir do histórico de trabalho na sessão atual —
reflete o estado do código no momento da geração, não substitui a
consulta ao repositório para a versão mais atual.*

