# GUIA SUPER DETALHADO: Deploy do Discord Mediação Bot na Square Cloud 🇧🇷

> Este guia foi escrito para quem **nunca fez deploy antes**.  
> Se você seguir cada passo, vai conseguir colocar seu sistema no ar. ✅

---

## ✅ Pré-requisitos (o que você precisa ter ANTES)

Antes de começar, confirme estes itens:

1. **Conta no Discord** com os tokens dos bots/clientes que você vai gerenciar.
2. **Projeto completo** em uma pasta (este projeto em `/home/ubuntu/discord-mediacao-bot`).
3. **Conta de banco de dados PostgreSQL externa** (recomendado: Supabase, Railway, Neon ou Render).
4. **Conta na Square Cloud** criada.
5. **Arquivo `.env` com dados reais** (não usar valores de exemplo em produção).
6. **Conexão de internet estável** para fazer upload sem falha.

💡 **Dica importante:** A Square Cloud não deve usar SQLite para produção multi-cliente. Use PostgreSQL remoto.

---

## 📝 Passo 1: Criar conta na Square Cloud

1. Acesse: **https://squarecloud.app/**
2. Clique em **Criar conta** / **Sign Up**.
3. Faça login com seu método preferido (geralmente Discord).
4. Confirme sua conta (se solicitado).
5. Entre no painel principal.

📸 Sugestão visual: procure no topo/botão algo como **"New Application"** ou **"Criar Aplicação"**.

---

## 📦 Passo 2: Preparar os arquivos do projeto

Dentro da pasta do projeto, você já deve ter estes arquivos principais para a Square Cloud:

- `squarecloud.config` ✅
- `start.sh` ✅
- `requirements.txt` ✅
- código fonte (`backend/`, `bot/`, `frontend/`) ✅

### 2.1) Conferir `squarecloud.config`
Este arquivo diz para a Square Cloud como iniciar seu app.

Exemplo usado neste projeto:

```ini
DISPLAY_NAME=Discord Mediacao Bot
MAIN=backend/main.py
MEMORY=1024
VERSION=recommended
START=bash start.sh
```

### 2.2) Conferir `.env`
Crie (ou ajuste) o arquivo `.env` com dados reais. Exemplo:

```env
DATABASE_URL=postgresql://USUARIO:SENHA@HOST:5432/NOME_DB
ADMIN_USERNAME=admin
ADMIN_PASSWORD=sua_senha_forte_aqui
SECRET_KEY=uma_chave_muito_grande_e_aleatoria
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
API_HOST=0.0.0.0
API_PORT=8000
```

⚠️ **Nunca compartilhe seu `.env` em local público.**

### 2.3) Compactar o projeto em ZIP
Você deve enviar um `.zip` para Square Cloud.

Inclua no ZIP:
- código do projeto
- `squarecloud.config`
- `start.sh`
- `.env` (se sua estratégia for enviar junto)

Não incluir:
- `venv/`
- `__pycache__/`
- arquivos temporários
- banco local (`mediacao.db`)

---

## ⬆️ Passo 3: Fazer upload na Square Cloud

1. No painel da Square Cloud, clique em **Nova Aplicação**.
2. Escolha o envio por arquivo `.zip`.
3. Selecione o ZIP que você acabou de criar.
4. Aguarde o upload terminar.
5. A aplicação aparecerá na sua lista.

🔎 Se der erro de upload, verifique:
- tamanho do ZIP
- internet
- se `squarecloud.config` está na **raiz** do ZIP

---

## ⚙️ Passo 4: Configurar variáveis de ambiente (.env)

Dependendo do fluxo da plataforma, você pode:

- enviar `.env` no ZIP, **ou**
- configurar variáveis direto no painel da Square Cloud (mais recomendado)

### Variáveis mínimas recomendadas:
- `DATABASE_URL`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `API_HOST`
- `API_PORT`

✅ Se a plataforma tiver aba de variáveis, prefira cadastrar por lá para facilitar troca sem novo upload.

---

## 🚀 Passo 5: Iniciar a aplicação

1. Abra sua aplicação no painel.
2. Clique em **Start** / **Iniciar**.
3. Acompanhe os logs ao vivo.

Você deve ver algo parecido com:

- instalação das dependências
- execução do `start.sh`
- `uvicorn backend.main:app ...`
- servidor iniciado na porta configurada

Se tudo estiver certo: ✅ app online.

---

## 🌐 Passo 6: Acessar a dashboard

Quando o deploy subir:

1. Copie a URL pública fornecida pela Square Cloud.
2. Abra no navegador.
3. Vá para a tela de login da dashboard.
4. Entre com `ADMIN_USERNAME` e `ADMIN_PASSWORD` do `.env`.
5. Cadastre seus clientes/bots no painel.

Depois disso você já consegue:
- criar clientes
- iniciar/parar bots
- ver logs
- acompanhar status

---

## ❓ Passo 7: Troubleshooting (problemas comuns)

### Problema: app não inicia
**Causa comum:** variável de ambiente faltando.  
**Solução:** revise `DATABASE_URL`, `SECRET_KEY`, usuário/senha admin.

### Problema: erro de banco de dados
**Causa comum:** `DATABASE_URL` inválida ou banco bloqueado por firewall.  
**Solução:** teste a URL no provedor e confirme usuário/senha/host/porta.

### Problema: dashboard abre mas não loga
**Causa comum:** `ADMIN_USERNAME` ou `ADMIN_PASSWORD` diferente do esperado.  
**Solução:** ajuste variáveis e reinicie aplicação.

### Problema: bot não conecta no Discord
**Causa comum:** token inválido ou expirado.  
**Solução:** gerar token válido e atualizar no painel.

### Problema: OCR falhando
**Causa comum:** falta de libs, imagem ruim, pouca memória.  
**Solução:** aumentar memória e melhorar qualidade dos prints.

### Problema: aplicação cai por memória
**Causa comum:** OCR + múltiplos bots consomem RAM.  
**Solução:** subir plano com mais memória (1024MB, 2048MB ou mais).

---

## 💰 Informações sobre planos e custos

Os valores mudam conforme a Square Cloud atualiza os planos.  
Então o ideal é sempre conferir diretamente no painel/site oficial.

Em geral, o preço varia por:
- memória RAM
- CPU
- quantidade de apps
- recursos extras

### Recomendação prática para este projeto
- **Mínimo:** 512MB (apenas cenário simples)
- **Recomendado:** 1024MB
- **Ideal para uso pesado com OCR + vários bots:** 2048MB+

---

## ✅ Resumo rápido (cola de bolso)

1. Criar conta Square Cloud 👤
2. Ajustar `.env` com dados reais 🔐
3. Garantir `squarecloud.config` e `start.sh` 📄
4. Compactar projeto em ZIP 📦
5. Upload no painel ⬆️
6. Configurar variáveis ⚙️
7. Iniciar app 🚀
8. Abrir URL e logar na dashboard 🌐

---

## 🎯 Dica final para iniciantes

Se der erro, não se preocupe. Quase sempre é:
- variável faltando
- banco com URL errada
- token inválido
- pouca memória

Vá por etapas e teste uma coisa por vez. Isso resolve 90% dos casos. 💪
