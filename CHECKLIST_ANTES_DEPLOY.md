# ✅ CHECKLIST ANTES DO DEPLOY (Square Cloud)

Use esta lista antes de enviar a aplicação para evitar erros.

## 🔐 Segurança e acessos

- [ ] Criei e revisei o arquivo `.env`
- [ ] Defini `ADMIN_USERNAME` e `ADMIN_PASSWORD` fortes
- [ ] Defini `SECRET_KEY` forte e aleatória
- [ ] Não vou expor meu `.env` em repositório público

## 🤖 Bots e credenciais

- [ ] Tokens dos bots/clientes estão configurados corretamente
- [ ] Tokens foram testados (sem erro de autenticação)
- [ ] Prefixo/comandos dos bots conferidos
- [ ] IDs de categoria/cargo (se usados) foram preenchidos

## 📧 E-mail e PIX

- [ ] E-mails dos clientes foram cadastrados
- [ ] Senhas de app dos e-mails foram cadastradas
- [ ] O acesso IMAP está habilitado no provedor de e-mail

## 🗄️ Banco de dados

- [ ] Tenho um banco PostgreSQL externo funcionando
- [ ] `DATABASE_URL` está correta no `.env`
- [ ] Banco de dados testado com sucesso

## 📦 Estrutura de arquivos

- [ ] Arquivo `squarecloud.config` existe na raiz
- [ ] Arquivo `start.sh` existe na raiz
- [ ] Arquivo `requirements.txt` atualizado
- [ ] O arquivo `.zip` foi gerado sem `venv/` e sem arquivos desnecessários

## ⚙️ Recursos da hospedagem

- [ ] Memória configurada (mínimo 512MB, recomendado 1024MB+)
- [ ] Estou ciente de que OCR pode exigir mais RAM
- [ ] Plano da Square Cloud escolhido é suficiente para a carga

## 🚀 Validação final

- [ ] Li o `GUIA_DEPLOY_SQUARE_CLOUD.md`
- [ ] Sei em qual URL a dashboard ficará disponível
- [ ] Tenho um plano de teste pós-deploy (login + criação de cliente + start bot)

---

## 🎯 Regra de ouro

Se qualquer item acima estiver sem marcar, **não faça deploy ainda**.  
Marque tudo primeiro para evitar retrabalho. ✅
