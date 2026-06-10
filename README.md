# Mediação Bot Multi-Cliente

Um sistema completo de bot de mediação para Discord que suporta múltiplos clientes simultaneamente rodando a partir de uma única aplicação e banco de dados. Conta com uma Dashboard Web em FastAPI + PostgreSQL.

## Funcionalidades
- Multi-Cliente (cada cliente roda em uma task assíncrona separada).
- Anti-Detecção (Rate limit, Delays aleatórios, Typing indicator simulado, User-Agents realistas).
- Integração Gmail para verificação de PIX.
- OCR para leitura de prints de comprovantes enviados no chat.
- Dashboard Administrativa para métricas, liga/desliga clientes, setup de credenciais, logs em tempo real.

## Requisitos

- Python 3.10+
- PostgreSQL
- Opcional: Docker e Docker Compose

## Instalação (Local)

1. Clone o repositório ou baixe os arquivos.
2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Crie o arquivo `.env` baseado no `.env.example`:
   ```bash
   cp .env.example .env
   # Edite as credenciais no .env, principalmente o DATABASE_URL e senha da Dashboard
   ```
5. Inicie a API e a Dashboard (o banco de dados será inicializado automaticamente):
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```

A dashboard estará disponível em `http://localhost:8000`. Conecte usando credenciais configuradas no `.env`.

## Rodar com Docker

Para iniciar tudo de forma rápida com o banco de dados via Docker:
```bash
docker-compose up --build -d
```

## Como configurar o cliente via Dashboard
1. Logue em `http://localhost:8000` (usuário: admin / senha: admin_super_secreta).
2. Clique em "Novo Cliente".
3. Forneça o Nome.
4. Forneça o **Token do Discord** (Aviso: Uso de self-bots viola os ToS do Discord).
5. Forneça o Email (Gmail) e a **Senha de App** para ler e-mails. (Para criar acesse: *Sua conta Google -> Segurança -> Verificação em duas etapas -> Senhas de app*).
6. Após criar o cliente, clique no botão "Iniciar" para ativar o bot.
