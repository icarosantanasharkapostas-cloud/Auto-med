# 📋 Comandos do Git — Copiar e Colar

Esta é uma "cola" com os comandos prontos. É só copiar e colar no terminal! 😉

> 📖 Se você é iniciante e quer o passo a passo explicado, leia o arquivo
> **`GUIA_GITHUB.md`** primeiro.

> 🗂️ **Importante:** sempre rode estes comandos **dentro da pasta do projeto**
> (a pasta `discord-mediacao-bot`).

---

## ⚙️ 1. Configuração inicial (só uma vez na vida)

Diz pro Git quem é você. Troque pelos seus dados:

```bash
git config --global user.name "Seu Nome"
git config --global user.email "seu-email@exemplo.com"
```

---

## 🚀 2. Primeiro envio pro GitHub (só uma vez por projeto)

⚠️ No passo 5, **troque a URL** pela URL do SEU repositório do GitHub!

```bash
git init
git add .
git commit -m "Primeiro envio do bot de mediacao"
git branch -M main
git remote add origin https://github.com/seu-usuario/discord-mediacao-bot.git
git push -u origin main
```

---

## 🔄 3. Atualizar o código (no dia a dia)

Sempre que mudar algo e quiser enviar pro GitHub:

```bash
git add .
git commit -m "Descreva aqui o que voce mudou"
git push
```

---

## 🔍 4. Comandos úteis do dia a dia

```bash
# Ver o que mudou / o que será enviado (use SEMPRE antes do push!)
git status

# Ver o histórico de envios (commits)
git log --oneline

# Baixar atualizações do GitHub pro seu PC
git pull

# Ver o endereço do repositório conectado
git remote -v

# Ver as mudanças exatas (linha por linha) ainda não commitadas
git diff
```

---

## 🛟 5. Comandos para resolver problemas

```bash
# "remote origin already exists" → remove a conexão antiga e refaz
git remote remove origin
git remote add origin https://github.com/seu-usuario/discord-mediacao-bot.git

# Tirar um arquivo enviado por engano do controle do Git
# (ex: se o .env foi adicionado sem querer ANTES de commitar)
git rm --cached .env

# Desfazer mudanças em um arquivo (volta como estava no ultimo commit)
git checkout -- nome-do-arquivo

# Ver qual branch você está
git branch
```

---

## 🔒 Lembrete de segurança

Antes de cada `git push`, rode `git status` e confira que o arquivo **`.env`**
**NÃO** está na lista de arquivos a serem enviados. Seus segredos devem ficar
sempre no seu computador! 🔐

> ✅ O `.gitignore` já protege o `.env`, o banco de dados local e outros arquivos
> sensíveis automaticamente.
