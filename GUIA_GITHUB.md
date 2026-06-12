# 🚀 Guia Completo: Colocando seu Bot no GitHub

Olá! 👋 Este guia foi feito para **iniciantes**. Vamos te ensinar, passo a passo,
como enviar o código do seu bot para o **GitHub** e, depois, conectá-lo à
**Square Cloud** para o deploy.

> 💡 **O que é o GitHub?** É como uma "nuvem" para guardar o código do seu projeto.
> Além de fazer backup, ele permite atualizar seu bot facilmente e conectar com
> serviços de hospedagem como a Square Cloud.

Não se preocupe se você nunca usou nada disso. É só seguir cada passo na ordem. 😉

---

## ✅ Antes de começar (pré-requisitos)

Você vai precisar de:

1. 📧 **Uma conta no GitHub** (gratuita). Crie em: https://github.com/signup
2. 💻 **O Git instalado** no seu computador. Para verificar se já tem, abra o
   terminal (Prompt de Comando no Windows) e digite:
   ```bash
   git --version
   ```
   - Se aparecer um número de versão (ex: `git version 2.40.0`), está tudo certo! ✅
   - Se der erro, baixe e instale aqui: https://git-scm.com/downloads

---

## 📦 Passo 1 — Criar o repositório no GitHub

Um "repositório" (ou "repo") é a pasta do seu projeto lá no GitHub.

1. Entre no site https://github.com e faça login.
2. No canto superior direito, clique no **`+`** e depois em **"New repository"**
   (Novo repositório). 🆕
3. Preencha os campos:
   - **Repository name** (nome): algo como `discord-mediacao-bot` 📝
   - **Description** (opcional): "Bot de mediação para Discord"
   - **Visibilidade**: escolha **Private** (Privado) 🔒 — assim só você vê o código.
     (Recomendado, pois é um projeto com configurações sensíveis.)
4. ⚠️ **NÃO marque** nenhuma das opções "Add a README", "Add .gitignore" ou
   "Choose a license". Deixe tudo desmarcado (nós já temos esses arquivos!).
5. Clique no botão verde **"Create repository"**. 🎉

Pronto! O GitHub vai te mostrar uma página com alguns comandos. **Não feche essa
página ainda** — vamos usar o endereço do repositório no Passo 3.

> 📌 O endereço será parecido com:
> `https://github.com/seu-usuario/discord-mediacao-bot.git`

---

## ⚙️ Passo 2 — Configurar o Git no seu computador

Isso só precisa ser feito **uma vez** (na primeira vez que você usa o Git).
É para o Git saber quem é você.

Abra o terminal **na pasta do seu projeto** e digite (trocando pelos seus dados):

```bash
git config --global user.name "Seu Nome"
git config --global user.email "seu-email@exemplo.com"
```

> 💡 Use o **mesmo email** que você usou para criar a conta no GitHub.

> 🗂️ **Como abrir o terminal na pasta do projeto?**
> - **Windows**: abra a pasta do projeto, clique com o botão direito em um espaço
>   vazio e escolha "Abrir no Terminal" (ou "Git Bash Here").
> - **Mac**: abra a pasta no Finder, clique com o botão direito e escolha
>   "Novo Terminal na Pasta".
> - **Linux**: clique com o botão direito dentro da pasta → "Abrir terminal aqui".

---

## 📤 Passo 3 — Enviar o código pro GitHub (primeiro envio)

Agora vamos enviar todos os arquivos do seu bot para o repositório que você criou.

No terminal, **dentro da pasta do projeto**, digite os comandos abaixo, **um por um**:

```bash
# 1. Inicia o controle de versão na pasta (cria um repositório local)
git init

# 2. Adiciona TODOS os arquivos (o .gitignore protege os segredos automaticamente)
git add .

# 3. Cria o primeiro "save" (commit) com uma mensagem
git commit -m "Primeiro envio do bot de mediacao"

# 4. Define o nome do branch principal como "main"
git branch -M main

# 5. Conecta sua pasta local ao repositório do GitHub
#    ⚠️ TROQUE a URL abaixo pela URL do SEU repositório (do Passo 1)!
git remote add origin https://github.com/seu-usuario/discord-mediacao-bot.git

# 6. Envia tudo pro GitHub! 🚀
git push -u origin main
```

> 🔑 **Vai pedir login?** Na hora do `git push`, o GitHub pode pedir seu usuário
> e senha. A "senha" hoje em dia **não é a senha da conta** — é um **token**.
> Veja como gerar um token no final deste guia (seção "❓ Problemas comuns").

✅ **Deu certo?** Atualize a página do seu repositório no GitHub. Todos os arquivos
do seu bot devem aparecer lá! 🎉

> 🔒 Repare que o arquivo `.env` (com seus segredos) **NÃO** aparece no GitHub.
> Isso é proposital e correto — o `.gitignore` o protegeu! ✅

---

## ☁️ Passo 4 — Conectar o GitHub com a Square Cloud

Agora que o código está no GitHub, vamos fazer a Square Cloud puxar ele de lá.

1. Entre no painel da Square Cloud: https://squarecloud.app e faça login.
2. Procure a opção de **criar/subir uma aplicação** e escolha a opção de
   **importar do GitHub** (geralmente chamada de "Deploy via GitHub" ou
   "Conectar repositório"). 🔗
3. A Square Cloud vai pedir para **autorizar o acesso** à sua conta do GitHub.
   Clique em autorizar e selecione o repositório `discord-mediacao-bot`. ✅
4. Confirme que o arquivo **`squarecloud.config`** está no projeto (ele já está! 👍).
   É ele que diz pra Square Cloud como rodar o bot.
5. ⚠️ **MUITO IMPORTANTE — configure as variáveis de ambiente!**
   Como o arquivo `.env` **não** foi pro GitHub (por segurança), você precisa
   cadastrar essas configurações **manualmente** no painel da Square Cloud.
   Procure a seção **"Environment Variables"** (Variáveis de Ambiente) e adicione
   cada uma das variáveis que estão no arquivo `.env.example`:
   - `DATABASE_URL`
   - `ADMIN_USERNAME`
   - `ADMIN_PASSWORD`
   - `SECRET_KEY`
   - `ALGORITHM`
   - `ACCESS_TOKEN_EXPIRE_MINUTES`
   - `API_HOST`
   - `API_PORT`

   Use os **valores reais** (não os de exemplo!) para cada uma. 🔐
6. Inicie o deploy. A Square Cloud vai baixar o código do GitHub e colocar seu
   bot no ar! 🚀

> 💡 **Vantagem de usar GitHub:** sempre que você atualizar o código (Passo 5),
> é muito mais fácil mandar a nova versão pra Square Cloud.

---

## 🔄 Passo 5 — Atualizar o código depois (no dia a dia)

Fez uma mudança no bot e quer enviar pro GitHub? É só seguir estes 3 comandos:

```bash
# 1. Adiciona as mudanças
git add .

# 2. Cria um "save" descrevendo o que você mudou
git commit -m "Descreva aqui o que voce mudou"

# 3. Envia pro GitHub
git push
```

Depois, atualize o deploy na Square Cloud (geralmente há um botão de
**"Redeploy"** ou ele atualiza sozinho quando detecta mudanças no GitHub). 🔁

---

## 🛡️ Avisos de Segurança (LEIA COM ATENÇÃO!)

A coisa mais importante deste guia: **NUNCA envie segredos para o GitHub!** 🔒

❌ **NUNCA suba para o GitHub:**
- O arquivo **`.env`** (ele tem suas senhas e chaves reais).
- **Tokens do Discord** dos clientes/contas.
- **Senhas** de banco de dados, da dashboard ou de qualquer serviço.
- A **`SECRET_KEY`** real.

✅ **O que te protege:**
- O arquivo **`.gitignore`** já está configurado para ignorar o `.env`, o banco
  de dados local e outros arquivos sensíveis automaticamente. 👏
- Sempre use o **`.env.example`** apenas como um MODELO (com valores falsos).

🚨 **E se eu mandei um segredo sem querer?**
1. Considere aquele segredo **comprometido** e **troque-o imediatamente**
   (gere um novo token do Discord, mude a senha, gere uma nova `SECRET_KEY`, etc).
2. Apague o arquivo do histórico do Git (peça ajuda se não souber como).
3. Não basta só apagar o arquivo num commit novo — o segredo fica no histórico!
   Por isso, **troque o segredo** é o passo mais importante.

💡 **Dica de ouro:** antes de cada `git push`, dê uma olhada com `git status`
para conferir o que está sendo enviado.

---

## ❓ Problemas comuns (Troubleshooting)

#### 🔑 "O GitHub está pedindo senha e a minha não funciona"
Desde 2021, o GitHub não aceita mais a senha da conta no terminal. Você precisa de
um **Personal Access Token (Token de Acesso Pessoal)**:
1. No GitHub, clique na sua foto (canto superior direito) → **Settings**.
2. Lá embaixo, no menu da esquerda: **Developer settings**.
3. **Personal access tokens** → **Tokens (classic)** → **Generate new token**.
4. Dê um nome, marque a opção **`repo`** e clique em gerar.
5. **Copie o token** (ele só aparece uma vez!) e use ele no lugar da senha quando
   o terminal pedir. 🔐

#### 🚫 "Erro: remote origin already exists"
Você já tinha conectado um repositório antes. Para corrigir, rode:
```bash
git remote remove origin
```
E depois repita o comando `git remote add origin ...` do Passo 3.

#### 📭 "Meus arquivos não aparecem no GitHub"
- Confira se você rodou o `git push` sem erros.
- Atualize (F5) a página do repositório no navegador.
- Rode `git status` para ver se há algo que não foi enviado (commitado).

#### 🤔 "Não sei se o .env foi enviado por engano"
No GitHub, procure pelo arquivo `.env` na lista de arquivos do repositório.
- Se **NÃO aparecer** → ótimo, está protegido! ✅
- Se **aparecer** → siga a seção "E se eu mandei um segredo sem querer?" acima. 🚨

---

## 📚 Arquivos relacionados

- **`COMANDOS_GIT.md`** → Lista de comandos prontos para copiar e colar. 📋
- **`.env.example`** → Modelo das variáveis de ambiente (sem segredos reais).
- **`GUIA_DEPLOY_SQUARE_CLOUD.md`** → Guia de deploy enviando um arquivo ZIP.
- **`CHECKLIST_ANTES_DEPLOY.md`** → Lista de verificação antes de subir o bot.

---

🎉 **Parabéns!** Agora seu bot está no GitHub e pronto para o deploy.
Qualquer dúvida, releia o passo com calma — você consegue! 💪
