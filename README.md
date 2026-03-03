# PA • Gemba Board ANDON — v10 (fix caminho do Excel)

**Fonte fixa:** `data/pa.xlsx`

## Correção do erro NotADirectoryError / FileNotFound
Esta versão:
- Resolve o caminho usando `Path(__file__).parent` (não depende do diretório atual)
- Detecta se existe um arquivo chamado `data` (errado) e mostra mensagem clara
- Faz fallback: procura qualquer `.xlsx` dentro de `data/` e no root do repo

## Atualizar dados
Substitua `data/pa.xlsx` no GitHub e faça commit/push.
