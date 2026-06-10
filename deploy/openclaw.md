# Deploy no OpenClaw / VPS Normal via Painel Web

O [OpenClaw](https://openclaw.com/) (e a maioria das VPS) funciona perfeitamente para esse sistema via Docker, recomendando utilizar a interface deles para configurar variáveis.

### Método 1: Usando Docker (Recomendado)

Sendo uma aplicação Multi-Container (API, Banco de dados e Worker juntos), a melhor maneira é utilizar o arquivo `docker-compose.yml` providenciado neste repositório.

1. Conecte no Terminal do seu OpenClaw.
2. Clone o repositório ou suba a pasta descompactada pelo File Manager.
3. Dentro da pasta principal, configure o `.env`.
4. Rode as instâncias com o banco de dados via comando docker:
```bash
docker compose build
docker compose up -d
```
A API será inicializada na porta 8000 e o banco de dados rodará na 5432 internamente na rede docker.

### Setup de Domínio (Nginx/Proxy Reverso)
Para expor a Dashboard num domínio (ex: `admin.bot.com`):
Instale o Nignx (`apt install nginx`), e crie um bloco em `/etc/nginx/sites-available/default`:

```nginx
server {
    listen 80;
    server_name admin.bot.com; # Seu IP do OpenCLaw ou dominio apontado

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
Não se esqueça de reiniciar o nginx: `sudo systemctl restart nginx`.


### Avisos Gerais de Hospedagem (OCR)
Bibliotecas de Machine Learning (como `easyocr` ou `pytorch`) demandam muita memória RAM. Para uma hospedagem estável, garanta no **mínimo 1.5GB a 2GB de RAM alocados** localmente para não passar por problemas de "Out Of Memory (OOM Kill) process".
