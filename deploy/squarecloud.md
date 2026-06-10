# Deploy na Square Cloud

A [Square Cloud](https://squarecloud.app/) suporta aplicações Python, porém este projeto requer um banco de dados PostgreSQL. Você deve usar um banco de dados externo compatível (como os oferecidos por ElephantSQL, Supabase, Render, ou até mesmo usar o banco de dados oficial do host se disponível).

### Passos de Instalação:

1. **Obtenha a URL do Banco de Dados Postgres:**
   Crie um banco de dados hospedado remotamente (Ex: Supabase) e copie o `DATABASE_URL`.

2. **Crie os arquivos necessários:**
   A Square Cloud necessita do arquivo `squarecloud.app`.
   Crie este arquivo na raiz do seu projeto `discord-mediacao-bot`:

   ```ini
   DISPLAY_NAME=MediacaoBot
   DESCRIPTION=Sistema multi-cliente de bots.
   MAIN=backend/main.py
   MEMORY=512
   VERSION=recommended
   START=uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```
   > **Nota:** OCR pode consumir muita RAM. Se for utilizá-lo frequentemente via EasyOCR, aumente o `MEMORY` para 1024 ou 2048 se seu plano permitir.

3. **Crie o arquivo `.env` para enviar junto (apenas em hosts seguros):**
   ```ini
   DATABASE_URL=postgresql://seu_usuario:sua_senha@seu_db_host:5432/seu_db
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=senha_forte_dashboard
   SECRET_KEY=uma_chave_aleatoria
   ```

4. **Compactar o projeto:**
   Selecione tudo dentro da pasta `discord-mediacao-bot`, exceto a pasta `venv` (ou `__pycache__`) e os arquivos do Git, e compacte em um arquivo formato `.zip`.

5. **Upload:**
   Vá no site da web dashboard da Square Cloud, clique em "New Application", suba o seu arquivo `.zip` e clique em iniciar.

Desta forma, os endpoints e o site estarão públicos na URL sub-domínio provida. Todos os bots carregarão as informações de forma invisível.
