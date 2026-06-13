# Guia de Implantação — Analisador de Contratos

Aplicação web (FastAPI) conteinerizada, portátil para qualquer infraestrutura
(Azure, AWS ou on-premise). Banco de dados em **Supabase/PostgreSQL**; LLM
configurável (em produção, **LLM privado no tenant do ME**).

## 1. Build e execução

```bash
# build da imagem
docker build -t analisador-contratos:latest .

# execução (passando as variáveis de ambiente do ambiente seguro)
docker run -d -p 8000:8000 --env-file .env \
  -v "$PWD/data:/app/data" -v "$PWD/relatorios:/app/relatorios" \
  analisador-contratos:latest

# OU, com docker compose:
docker compose up -d --build
```

A aplicação sobe em `http://<host>:8000` (interface em `/`, API/Swagger em `/docs`,
health-check em `/health`). As tabelas do banco são criadas automaticamente no arranque.

## 2. Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `DATABASE_URL` | sim | Connection string do Supabase/PostgreSQL (`postgresql://...`). |
| `LLM_PROVIDER` | sim | `azure` (produção), `openai_compat` ou `openrouter` (dev). |
| `SUPABASE_ANON_KEY` | sim | Chave pública do Supabase (login da interface). |
| `CURADOR_EMAILS` | sim | E-mails com papel de curador (separados por vírgula). |
| `SUPABASE_URL` | opcional | Derivada da `DATABASE_URL`; defina para sobrepor. |

**Se `LLM_PROVIDER=azure`:** `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`,
`AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION`.
**Se `openai_compat`:** `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`.

> Em produção, **não** use um arquivo `.env` no disco — injete as variáveis pelo
> mecanismo seguro da plataforma (Azure App Settings / Key Vault, AWS Secrets
> Manager, secrets do orquestrador, etc.).

## 3. Persistência

- **Banco** (usuários via Supabase Auth, base de conhecimento, análises): no Supabase.
- **Arquivos** (`/app/data/uploads`, `/app/relatorios`): hoje em volume local. Para
  produção multi-instância, migrar para storage gerenciado (Supabase Storage / Azure
  Blob / S3) — ponto de evolução já previsto.

## 4. Rede / TLS

- A aplicação serve HTTP na porta 8000. Coloque atrás de um **proxy reverso com HTTPS**
  (Nginx, Azure Front Door, ALB, Ingress) — necessário para uso corporativo e para o SSO.

## 5. Próximo passo: login Microsoft (SSO Entra)

Depende de itens do ambiente do ME (não do código):

1. **TI/Identidade do ME**: registrar um aplicativo SSO (SAML 2.0 ou OIDC) no tenant
   **Microsoft Entra ID**, apontando o redirect para a URL hospedada da aplicação.
2. **Supabase**: configurar o provedor SSO (Authentication → SSO) com os metadados do Entra.
3. **Código**: nenhuma mudança estrutural — a API já valida o JWT do Supabase. Os papéis
   continuam por `CURADOR_EMAILS` (ou evoluímos para uma tela admin de usuários).

## 6. Escala (quando necessário)

- Subir mais workers: `uvicorn app.api.main:app --workers N` (ou múltiplas réplicas do contêiner).
- O processamento de análise hoje roda em segundo plano no próprio processo; para alto
  volume, externalizar para uma fila (Redis + arq/Celery) — evolução já mapeada.
