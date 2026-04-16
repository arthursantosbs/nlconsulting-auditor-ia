# Checklist de Entrega

Este projeto ja esta pronto localmente. Os itens abaixo sao os passos externos que ainda precisam ser concluidos para a submissao final da vaga.

## 1. Processar o lote oficial

Assim que voce tiver o `arquivos_nf.zip`, execute:

```bash
python scripts/process_batch.py "C:\caminho\para\arquivos_nf.zip"
```

Conferir os artefatos em `manual_runs/arquivos_nf/`:

- `results.csv`
- `anomalies.csv`
- `audit_log.csv`
- `results.xlsx`
- `summary.json`
- `anomaly_report.md`

## 2. Publicar no GitHub

Nao existe ferramenta de criacao de repositório GitHub disponivel neste ambiente. Entao sera preciso:

1. Criar um novo repositório publico, por exemplo: `nlconsulting-document-auditor`
2. Adicionar o remoto localmente
3. Fazer `git push`

Comandos sugeridos:

```bash
git remote add origin https://github.com/SEU_USUARIO/nlconsulting-document-auditor.git
git push -u origin main
```

## 3. Publicar a aplicacao no Render

Baseado na documentacao atual da Render:

- um Web Service recebe uma URL publica `onrender.com`
- a aplicacao precisa escutar em `0.0.0.0`
- deploy automatico funciona a partir de um branch conectado do GitHub

Passos:

1. No Render, criar um `Web Service`
2. Conectar o repositório GitHub publicado
3. Confirmar `buildCommand`: `pip install -r requirements.txt`
4. Confirmar `startCommand`: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Definir `OPENAI_API_KEY` nas environment variables
6. Fazer o primeiro deploy
7. Testar a URL publica gerada

Arquivos uteis:

- [render.yaml](/C:/Users/arthur/Desktop/NLConsulting/render.yaml)
- [Dockerfile](/C:/Users/arthur/Desktop/NLConsulting/Dockerfile)

## 4. Montar e publicar o Power BI

Baseado na documentacao atual da Microsoft:

- relatorios podem ser criados no Power BI Desktop e publicados no Power BI Service
- links compartilhados no Service dependem das permissoes/licenca do ambiente
- `Publish to web` torna o relatorio publico para qualquer pessoa na internet, entao use apenas se o dataset puder ser exposto

Passos:

1. Abrir o Power BI Desktop
2. Importar `results.csv`, `anomalies.csv` e `audit_log.csv`
3. Montar os visuais obrigatorios do briefing
4. Importar o tema [powerbi/theme.json](/C:/Users/arthur/Desktop/NLConsulting/powerbi/theme.json)
5. Publicar no Power BI Service
6. Obter o link do relatorio compartilhado
7. Se a sua conta nao permitir link publico, salvar e incluir o `.pbix` no repositório

Guia complementar:

- [powerbi/README.md](/C:/Users/arthur/Desktop/NLConsulting/powerbi/README.md)

## 5. Preparar a submissao por e-mail

Itens para enviar:

- URL publica da aplicacao
- link do GitHub publico
- link do Power BI Service ou arquivo `.pbix`
- breve texto com as anomalias encontradas com base em `anomaly_report.md`

## 6. Preparar a demo ao vivo

Treinar:

- upload de um arquivo novo
- explicacao do pipeline
- onde o prompt e a versao ficam registrados
- como o sistema lida com rate limit, timeout e encoding invalido
- como os CSVs alimentam o Power BI
