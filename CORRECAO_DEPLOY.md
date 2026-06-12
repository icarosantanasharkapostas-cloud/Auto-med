# 🔧 Correção do Erro de Deploy na Square Cloud

Olá! 👋 Este documento explica, de forma simples, **por que o deploy falhou** e
**o que foi corrigido** para resolver. No final, tem o passo a passo para você
fazer o **redeploy** (subir de novo) na Square Cloud. 🚀

---

## ❌ O que causou o erro?

Quando você subiu o bot, a Square Cloud usou o **Python 3.13** (a versão mais
nova). Aí apareceram dois erros no log:

```
TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'
...
maturin failed - Caused by: Failed to build a native library through cargo
```

Traduzindo para o português simples, aconteceram **dois problemas**:

1. 🧩 **Versões incompatíveis com o Python 3.13**
   Algumas bibliotecas estavam "presas" em versões antigas que **não funcionam**
   com o Python 3.13. Por isso apareceu o erro do `ForwardRef._evaluate()`.

2. 🦀 **Tentativa de compilar bibliotecas pesadas (erro do `cargo`/`maturin`)**
   - A biblioteca **`pydantic`** (na versão antiga) não tinha uma versão pronta
     para o Python 3.13, então o servidor tentava **compilar** ela do zero usando
     a linguagem Rust (`cargo`) — e isso falhava.
   - A biblioteca de OCR **`easyocr`** é muito pesada: ela baixa o **`torch`**
     (vários GB!) e também tenta compilar coisas. Isso estoura a memória e o
     tempo do deploy.

> 💡 **Resumindo:** as bibliotecas eram velhas demais ou pesadas demais para o
> ambiente da Square Cloud com Python 3.13.

---

## ✅ O que foi corrigido?

Fizemos **2 mudanças** no projeto para resolver tudo:

### 1. 📦 Atualizamos o `requirements.txt`
Trocamos todas as bibliotecas por **versões modernas e compatíveis com o
Python 3.13**. Todas elas agora têm versões "prontas" (chamadas de *wheels*),
ou seja, **não precisam ser compiladas** — o que elimina o erro do `cargo`.

Principais mudanças:

| Biblioteca | Antes ❌ | Agora ✅ |
|------------|---------|---------|
| `pydantic` | 2.3.0 (compilava no 3.13) | **2.9.2** (pronta p/ 3.13) |
| `fastapi` | 0.103.1 | **0.115.2** |
| `aiohttp` | < 3.8.0 (antiga) | **3.10.10** |
| `discord.py-self` | 1.9.2 | **2.0.0** |
| OCR | `easyocr` (puxava o torch 🐘) | **`pytesseract`** (leve 🪶) |

> 🔒 Mantivemos as bibliotecas que o seu código realmente usa: `PyJWT` (login),
> `imap-tools` (e-mail) e `psycopg2-binary` (banco PostgreSQL).

### 2. 🖼️ Trocamos o motor de OCR (leitura de texto em imagens)
- **Antes:** usávamos o `easyocr`, que baixava o `torch` (enorme) e compilava
  bibliotecas — causa principal da falha de memória/compilação.
- **Agora:** usamos o `pytesseract`, que é **leve** e usa o programa
  **Tesseract OCR** já instalado automaticamente pelo arquivo `start.sh`.
- O arquivo `bot/services/ocr_service.py` foi reescrito para usar o
  `pytesseract`. O resto do bot continua funcionando igual. 👍

> ✅ Testamos: o código novo de OCR foi importado e compilado sem erros.

---

## 🔄 Como fazer o redeploy (subir de novo)

Como você já conectou o projeto via GitHub, é bem rápido! 😉

### Opção A — Enviar a correção pro GitHub (recomendado)

As mudanças **já foram enviadas pro GitHub** automaticamente (commit + push).
Então no painel da Square Cloud você só precisa mandar atualizar:

1. Entre no painel da sua aplicação na Square Cloud: https://squarecloud.app
2. Abra a aplicação **"Discord Mediacao Bot"**.
3. Procure a opção de **"Commits"** / **"GitHub"** / **"Redeploy"** e clique para
   **puxar a versão mais nova do GitHub** e reiniciar o deploy. 🔁
4. Acompanhe os logs — desta vez **não deve aparecer** o erro do `cargo`/`maturin`. ✅

### Opção B — Subir um novo arquivo ZIP

Se preferir subir manualmente (sem o GitHub):

1. Compacte a pasta do projeto em um arquivo `.zip` (sem a pasta `venv` nem o
   arquivo `.env`).
2. No painel da Square Cloud, vá em **"Enviar aplicação"** (ou "Commit/Arquivos")
   e envie o novo `.zip`.
3. A aplicação será reiniciada com as correções. ✅

> ⏳ **Dica:** o primeiro deploy depois da correção pode demorar alguns minutos,
> pois a Square Cloud vai baixar as novas bibliotecas. É normal!

---

## 🔍 Como saber se deu certo?

Depois do redeploy, abra os **logs** da aplicação na Square Cloud e procure por:

- ✅ **Bom sinal:** mensagens como `Application startup complete` ou
  `Uvicorn running on...` e **nenhum** erro vermelho de `cargo`/`maturin`.
- ❌ **Se ainda der erro:** copie a mensagem do log e me mande aqui que eu te ajudo.

> 🌐 Lembre-se: como sua aplicação é um site/API, confira que as variáveis
> `API_HOST=0.0.0.0` e `API_PORT=80` (ou a porta que a Square Cloud indicar)
> estão configuradas, conforme o aviso que apareceu no deploy.

---

## 🛡️ Lembrete importante

Não esqueça de configurar as **variáveis de ambiente** no painel da Square Cloud
(elas não vêm do GitHub por segurança). Use o botão **"Importar do .env.example"**
para facilitar, e depois troque pelos seus **valores reais**. 🔐

---

## 📚 Arquivos relacionados

- **`requirements.txt`** → Lista de bibliotecas corrigida.
- **`GUIA_GITHUB.md`** → Como atualizar o código no GitHub.
- **`GUIA_DEPLOY_SQUARE_CLOUD.md`** → Guia completo de deploy.
- **`CHECKLIST_ANTES_DEPLOY.md`** → Lista de verificação antes de subir.

---

🎉 **Pronto!** Com essas correções, o deploy deve funcionar. Qualquer dúvida,
é só chamar. Você consegue! 💪
