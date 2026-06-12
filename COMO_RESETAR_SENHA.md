# 🔑 Como Resetar a Senha do Admin (Destravar o Login)

Olá! 👋 Este guia resolve o problema de **"Credenciais inválidas"** na tela de
login da dashboard. Tem **dois jeitos** de resolver — escolha o mais fácil pra você. 😉

---

## 🤔 Qual era o problema?

A tela de login estava recusando seu usuário e senha (mensagem
**"Credenciais inválidas"** 🔴).

Isso aconteceu porque o login dependia **só** das variáveis de ambiente
`ADMIN_USERNAME` e `ADMIN_PASSWORD`, e elas **não estavam corretas** na Square Cloud
(os valores acabaram se misturando/embaralhando no painel).

### ✅ O que foi corrigido no código
Agora o login aceita **duas formas** de entrar (basta uma funcionar):
1. 🌿 Pelas variáveis de ambiente (`ADMIN_USERNAME` / `ADMIN_PASSWORD`), como antes.
2. 🗄️ Por um **admin salvo no banco de dados** — criado por um dos métodos abaixo.
   A senha fica guardada com **hash** (criptografada), nunca em texto puro. 🔒

---

## 🚀 MÉTODO 1 — O jeito mais fácil (pelo navegador)

Criamos um "atalho" temporário que cria o admin pra você. É só abrir um link! 🔗

### Passo a passo:

1. Abra o navegador e acesse este endereço (troque pelo endereço do **seu** site):

   ```
   https://primeautomated.squareweb.app/api/setup-admin
   ```

   > 💡 É só pegar o endereço do seu site e adicionar **`/api/setup-admin`** no final.

2. Vai aparecer uma mensagem assim (em formato de texto/JSON):

   ```json
   {
     "success": true,
     "message": "Admin 'admin' criado com sucesso!",
     "username": "admin",
     "password": "admin123",
     "aviso": "Faça login com essas credenciais e TROQUE a senha depois..."
   }
   ```

   ✅ Pronto! O usuário admin foi criado no banco de dados.

3. Agora vá para a tela de login e entre com as credenciais padrão:

   | Campo | Valor |
   |-------|-------|
   | 👤 **Usuário** | `admin` |
   | 🔑 **Senha** | `admin123` |

4. 🎉 Você deve conseguir entrar na dashboard!

---

## 🛠️ MÉTODO 2 — Pelo Console da Square Cloud (terminal)

Se preferir (ou se o Método 1 não funcionar), use o script que criamos.

### Passo a passo:

1. No painel da Square Cloud, abra a sua aplicação **"Discord Mediacao Bot"**.
2. Procure a opção de **Terminal / Console** da aplicação.
3. Digite o comando abaixo e aperte Enter:

   ```bash
   python3 reset_admin.py
   ```

4. Vai aparecer uma mensagem confirmando, com o usuário e a senha:

   ```
   ✅ Usuário admin CRIADO com sucesso!
     👤 Usuário: admin
     🔑 Senha:   admin123
   ```

5. Agora é só fazer login com `admin` / `admin123`. ✅

> 💡 **Quer usar outro usuário/senha?** O script aceita valores personalizados:
> ```bash
> python3 reset_admin.py meu_usuario minha_senha_forte
> ```

---

## 🔐 Credenciais padrão que serão criadas

| Campo | Valor padrão |
|-------|--------------|
| 👤 Usuário | **`admin`** |
| 🔑 Senha | **`admin123`** |

---

## ⚠️ MUITO IMPORTANTE — Faça isso depois de entrar!

A senha `admin123` é **fraca** e serve só para destravar o acesso. Por segurança:

### 1. 🔁 Troque a senha por uma forte
Crie uma senha nova e segura. Você pode:
- Rodar de novo o script com a nova senha:
  ```bash
  python3 reset_admin.py admin sua_nova_senha_bem_forte
  ```
- **OU** configurar corretamente as variáveis `ADMIN_USERNAME` e `ADMIN_PASSWORD`
  no painel da Square Cloud (cada uma no seu campo certo, sem misturar valores!).

### 2. 🗑️ Remova o atalho temporário `/setup-admin`
O endereço `/api/setup-admin` é **temporário e inseguro** (qualquer pessoa que
souber o link pode usar). Depois de destravar o login, **apague-o do código**:

1. Abra o arquivo **`backend/api/routes.py`**.
2. Apague todo o bloco da função **`setup_admin`** (está marcado com
   `⚠️ ENDPOINT TEMPORÁRIO - REMOVER APÓS O PRIMEIRO USO!`).
3. Salve, faça `git commit` e `git push`, e atualize o deploy na Square Cloud.

> 💡 Não precisa apagar o `reset_admin.py` — ele só roda no terminal e é seguro
> deixar no projeto para usos futuros. Mas pode apagar se quiser. 👍

---

## ❓ Problemas comuns

#### 🔴 "Acessei /api/setup-admin mas deu erro"
- Confira se o endereço está certo (com `/api/setup-admin` no final).
- A aplicação precisa estar **online** na Square Cloud.
- Se o deploy ainda não atualizou com o código novo, faça o **redeploy**
  (puxe a versão mais nova do GitHub) e tente de novo.

#### 🔴 "Criei o admin mas ainda dá 'Credenciais inválidas'"
- Confira se digitou **exatamente** `admin` e `admin123` (sem espaços).
- Verifique se a aplicação foi reiniciada/atualizada com o código novo.
- Confirme que o `DATABASE_URL` é o **mesmo** usado pela aplicação (se você usa
  SQLite local, o arquivo do banco precisa ser o mesmo).

#### 🔴 "python3 reset_admin.py: No module named 'passlib'"
- As dependências precisam estar instaladas. Rode antes:
  ```bash
  pip install -r requirements.txt
  ```

---

## 📚 Arquivos relacionados

- **`reset_admin.py`** → Script que cria/redefine o admin pelo terminal.
- **`backend/api/routes.py`** → Onde fica o login e o endpoint temporário.
- **`.env.example`** → Modelo das variáveis (`ADMIN_USERNAME`, `ADMIN_PASSWORD`).
- **`GUIA_DEPLOY_SQUARE_CLOUD.md`** → Guia de deploy.

---

🎉 **Pronto!** Com isso você destrava o login. Não esqueça de **trocar a senha**
e **remover o `/setup-admin`** depois. Qualquer dúvida, é só chamar! 💪
