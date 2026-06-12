# 🔄 Como Atualizar o Código no GitHub

Olá! 👋 Este guia mostra, de forma **bem simples**, como enviar suas mudanças
para o GitHub sempre que você mexer no código do bot.

> 📍 Seu repositório: https://github.com/icarosantanasharkapostas-cloud/Auto-med

> 🗂️ **Lembre-se:** todos os comandos devem ser executados **dentro da pasta do
> projeto** (a pasta `discord-mediacao-bot`).

---

## 🚀 Passo a passo para enviar suas mudanças

Toda vez que você mudar algo no código e quiser salvar no GitHub, faça assim:

```bash
# 1. Veja o que você mudou (opcional, mas recomendado)
git status

# 2. Adiciona TODAS as mudanças
git add .

# 3. Cria um "save" (commit) descrevendo o que mudou
git commit -m "Descreva aqui o que voce mudou"

# 4. Envia tudo pro GitHub
git push
```

✅ Pronto! Suas mudanças já estão no GitHub. 🎉

> 💡 **Dica:** na mensagem do commit (passo 3), escreva algo curto e claro sobre
> o que você fez. Exemplos:
> - `"Corrige erro no login da dashboard"`
> - `"Adiciona novo comando no bot"`
> - `"Atualiza texto da mensagem de boas-vindas"`

---

## 📥 Baixar mudanças do GitHub (se você editou em outro lugar)

Se você (ou alguém) editou o código direto no site do GitHub ou em outro
computador, baixe as novidades pro seu PC antes de continuar trabalhando:

```bash
git pull
```

> 💡 **Boa prática:** rode `git pull` ANTES de começar a trabalhar. Isso evita
> conflitos (explicados abaixo). 😉

---

## ⚔️ Como resolver conflitos básicos

Um "conflito" acontece quando você e o GitHub mudaram a **mesma linha** de um
arquivo de jeitos diferentes. O Git não sabe qual versão manter e pede sua ajuda.

### 😱 Como sei que tenho um conflito?
Ao rodar `git pull` ou `git push`, aparece uma mensagem tipo:
```
CONFLICT (content): Merge conflict in nome-do-arquivo.py
```

### 🛠️ Como resolver (passo a passo):

1. **Abra o arquivo** que deu conflito (o nome aparece na mensagem).
2. Procure por marcações estranhas assim:
   ```
   <<<<<<< HEAD
   (a SUA versão da linha está aqui)
   =======
   (a versão que veio do GitHub está aqui)
   >>>>>>> origin/main
   ```
3. **Decida qual versão manter** (ou junte as duas) e **apague as marcações**
   `<<<<<<<`, `=======` e `>>>>>>>`. O arquivo deve ficar só com o texto correto.
4. Salve o arquivo.
5. Finalize o conflito com os comandos:
   ```bash
   git add .
   git commit -m "Resolve conflito"
   git push
   ```

✅ Conflito resolvido! 🎉

> 🆘 **Ficou perdido com um conflito?** Calma! Se quiser **descartar suas mudanças
> locais** e manter o que está no GitHub, você pode usar (CUIDADO: isso apaga o
> que você mudou localmente naquele arquivo):
> ```bash
> git checkout --theirs nome-do-arquivo
> git add .
> git commit -m "Resolve conflito mantendo versao do GitHub"
> ```

---

## 🔒 Lembrete de segurança (MUITO importante!)

Antes de cada `git push`, rode `git status` e confira que o arquivo **`.env`**
**NÃO** está na lista de arquivos a serem enviados.

❌ **NUNCA envie pro GitHub:**
- O arquivo `.env` (com suas senhas e tokens reais)
- Tokens do Discord
- Senhas de banco de dados

✅ O arquivo `.gitignore` já protege esses arquivos automaticamente. 👏

---

## ❓ Problemas comuns

#### 🔑 "Pediu login e a senha não funciona"
O GitHub não aceita mais a senha da conta no terminal — você precisa de um
**Personal Access Token**. Veja como criar um na seção de troubleshooting do
arquivo **`GUIA_GITHUB.md`**. 🔐

#### 🚫 "Erro: failed to push some refs / rejected"
Geralmente significa que há mudanças no GitHub que você ainda não baixou.
Resolva assim:
```bash
git pull
# (resolva conflitos, se aparecerem)
git push
```

#### 📭 "Minhas mudanças não aparecem no GitHub"
- Confira se você rodou `git push` sem erros.
- Rode `git status` para ver se ainda há algo não enviado.
- Atualize (F5) a página do repositório no navegador.

---

## 📚 Arquivos relacionados

- **`GUIA_GITHUB.md`** → Guia completo do primeiro envio e do deploy.
- **`COMANDOS_GIT.md`** → Cola de comandos prontos para copiar e colar.
- **`.env.example`** → Modelo das variáveis de ambiente (sem segredos).

---

💪 **É isso!** Atualizar o código é só `add` → `commit` → `push`. Com o tempo vira
rotina. Qualquer dúvida, releia com calma. Você consegue! 😊
