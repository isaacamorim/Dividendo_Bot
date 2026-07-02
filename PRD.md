# PRD — Dividend Bot B3 · Plataforma Web Completa

**Versão:** 1.0  
**Servidor:** 191.252.217.250 (mesmo VPS do Tradeon)  
**Repositório:** https://github.com/isaacamorim/Dividendo_Bot  
**Uso:** Pessoal + amigos convidados  
**Autenticação:** Senha simples (sem OAuth)  
**Alertas:** Via painel web (sem Telegram por enquanto)

---

## 1. Visão Geral

O Dividend Bot hoje é um scanner de terminal que roda manualmente. O objetivo deste PRD é transformá-lo numa plataforma web completa rodando 24/7 no VPS, com:

- Dashboard web acessível por navegador
- Scan automático diário sem intervenção manual
- Histórico de scores e sinais no tempo
- Gestão de carteira com rentabilidade ao vivo
- Backtest visualizado em gráficos
- Acesso por senha para uso pessoal e amigos

O core Python existente (análise, valuation, score) **não muda** — o back-end apenas o chama e serve os resultados via API.

---

## 2. Stack Técnica

### Back-end
- **Python 3.13** + **FastAPI** — API REST
- **PostgreSQL 15** — banco principal (substitui SQLite)
- **SQLAlchemy 2.0** — ORM
- **APScheduler** — cron interno (scan diário automático)
- **Uvicorn** — ASGI server
- **python-jose** + **passlib** — autenticação JWT simples

### Front-end
- **Next.js 14** (App Router)
- **Tailwind CSS** — estilo
- **Recharts** — gráficos (scores no tempo, backtest, carteira)
- **shadcn/ui** — componentes

### Infra (VPS 191.252.217.250)
- **Nginx** — reverse proxy (porta 80/443 → serviços internos)
- **systemd** — gerencia os serviços (API + Next.js)
- **Certbot** — SSL gratuito (Let's Encrypt)
- **PM2** — gerencia o processo Next.js (já usado no Tradeon)
- **GitHub Actions** — CI/CD: push em main → deploy automático no VPS

### Portas (não conflitar com Tradeon)
| Serviço | Porta interna |
|---|---|
| FastAPI | 8001 |
| Next.js | 3002 |
| PostgreSQL | 5432 (já existe, novo banco) |

---

## 3. Estrutura de Diretórios (pós-migração)

```
Dividendo_Bot/
│
├── backend/                    # FastAPI
│   ├── main.py                 # entrypoint FastAPI
│   ├── routers/
│   │   ├── auth.py             # login / token
│   │   ├── scan.py             # GET /scan, POST /scan/run
│   │   ├── carteira.py         # CRUD carteira
│   │   ├── backtest.py         # GET /backtest/{ticker}
│   │   └── historico.py        # GET /historico/{ticker}
│   ├── models/                 # SQLAlchemy models
│   │   ├── snapshot.py         # score diário por ticker
│   │   ├── carteira.py         # posições e dividendos
│   │   └── user.py             # usuários (senha hash)
│   ├── schemas/                # Pydantic schemas (request/response)
│   ├── db.py                   # conexão PostgreSQL
│   ├── scheduler.py            # APScheduler — scan diário 7h
│   └── requirements.txt
│
├── frontend/                   # Next.js
│   ├── app/
│   │   ├── page.tsx            # redireciona → /login ou /dashboard
│   │   ├── login/page.tsx      # tela de login
│   │   └── dashboard/
│   │       ├── page.tsx        # scan + top 5
│   │       ├── carteira/       # gestão de carteira
│   │       ├── backtest/       # visualização de backtest
│   │       └── historico/      # evolução de score no tempo
│   ├── components/
│   │   ├── ScanTable.tsx       # tabela principal
│   │   ├── Top5Cards.tsx       # cards top 5
│   │   ├── ScoreChart.tsx      # gráfico score no tempo
│   │   ├── CarteiraTable.tsx   # posições com rentabilidade
│   │   └── BacktestChart.tsx   # gráfico capital ao longo do tempo
│   └── package.json
│
├── core/                       # código Python existente (sem alteração)
│   ├── config/
│   ├── data/
│   ├── analysis/
│   ├── backtest/
│   ├── portfolio/
│   └── reports/
│
├── tests/                      # testes
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── .github/workflows/
│   └── deploy.yml              # CI/CD
│
├── nginx/
│   └── dividendo_bot.conf      # config nginx
│
├── .env.example                # variáveis de ambiente documentadas
└── PRD.md                      # este arquivo
```

---

## 4. Banco de Dados

### 4.1 Tabelas

```sql
-- Usuários (autenticação simples)
CREATE TABLE users (
    id          SERIAL PRIMARY KEY,
    username    VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Snapshot diário de cada ativo
CREATE TABLE snapshots (
    id              SERIAL PRIMARY KEY,
    ticker          VARCHAR(10) NOT NULL,
    data            DATE NOT NULL,
    preco           NUMERIC(10,2),
    preco_justo     NUMERIC(10,2),
    upside          NUMERIC(6,2),
    dy              NUMERIC(6,2),
    roe             NUMERIC(6,2),
    pl              NUMERIC(8,2),
    score           NUMERIC(4,2),
    sinal           VARCHAR(10),
    estrategia      VARCHAR(15),
    setor_perfil    VARCHAR(30),
    div_estimado    NUMERIC(8,2),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(ticker, data)          -- um snapshot por ativo por dia
);

-- Posições da carteira
CREATE TABLE posicoes (
    id          SERIAL PRIMARY KEY,
    ticker      VARCHAR(10) NOT NULL,
    data_compra DATE NOT NULL,
    preco_compra NUMERIC(10,2) NOT NULL,
    quantidade  INTEGER NOT NULL,
    nota        TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Dividendos recebidos
CREATE TABLE dividendos_recebidos (
    id              SERIAL PRIMARY KEY,
    ticker          VARCHAR(10) NOT NULL,
    data_pagamento  DATE NOT NULL,
    valor_por_acao  NUMERIC(8,4) NOT NULL,
    quantidade      INTEGER NOT NULL,
    total           NUMERIC(10,2) NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Resultados de backtest (cache)
CREATE TABLE backtest_runs (
    id              SERIAL PRIMARY KEY,
    ticker          VARCHAR(10) NOT NULL,
    periodo         VARCHAR(10) NOT NULL,
    retorno_pct     NUMERIC(8,2),
    cagr_pct        NUMERIC(8,2),
    sharpe          NUMERIC(6,3),
    max_drawdown    NUMERIC(8,2),
    alpha_pct       NUMERIC(8,2),
    win_rate_pct    NUMERIC(6,2),
    n_trades        INTEGER,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(ticker, periodo)
);
```

### 4.2 Índices necessários
```sql
CREATE INDEX idx_snapshots_ticker_data ON snapshots(ticker, data DESC);
CREATE INDEX idx_posicoes_ticker ON posicoes(ticker);
CREATE INDEX idx_dividendos_ticker ON dividendos_recebidos(ticker);
```

---

## 5. API — Endpoints

### Autenticação
```
POST /auth/login
  body: { username, password }
  return: { access_token, token_type }
  
  Todas as rotas abaixo exigem header:
  Authorization: Bearer <token>
```

### Scan
```
GET  /scan/latest
  Retorna o último snapshot de cada ativo (do banco).
  Se não houver snapshot de hoje: roda o scan ao vivo e salva.
  return: { data, resultados: [...], top5: [...] }

POST /scan/run
  Força scan ao vivo agora (independente de horário).
  return: { status: "ok", resultados: [...] }

GET  /scan/historico/{ticker}?dias=30
  Evolução de score, sinal, preco, upside nos últimos N dias.
  return: { ticker, serie: [{ data, score, sinal, preco, upside }] }
```

### Carteira
```
GET    /carteira
  Retorna posições com preço atual (yfinance) + rentabilidade.
  return: { posicoes: [...], resumo: { total_investido, total_atual, 
            rentabilidade_pct, total_dividendos, rent_total_pct } }

POST   /carteira/posicao
  body: { ticker, preco_compra, quantidade, data_compra, nota? }
  return: posicao criada

DELETE /carteira/posicao/{id}
  Remove posição pelo id.

POST   /carteira/dividendo
  body: { ticker, valor_por_acao, data_pagamento }
  return: dividendo registrado

GET    /carteira/dividendos?ticker=PETR4
  Lista dividendos recebidos, filtro opcional por ticker.
```

### Backtest
```
GET /backtest/{ticker}?periodo=5y
  Roda backtest ou retorna do cache (< 24h).
  return: resultado completo com trades e histórico de capital

GET /backtest/comparativo
  Roda backtest em todos os tickers da watchlist e retorna ranking.
  return: { resultados: [...], alpha_medio, pct_venceu_bh }
```

---

## 6. Front-end — Telas e Componentes

### 6.1 Login (`/login`)
- Campo usuário + senha
- Botão entrar
- Erro claro se credenciais erradas
- Redireciona para `/dashboard` após login
- Token guardado em cookie httpOnly (seguro)

### 6.2 Dashboard (`/dashboard`)
**Seção 1 — KPIs do scan**
- Cards: total analisado · BUY · HOLD · SELL · última atualização

**Seção 2 — Top 5 Oportunidades**
- 5 cards com: ticker, sinal colorido, score, DY, upside, div/ano, estratégia

**Seção 3 — Tabela de scan**
- Colunas: Ticker · Nome · Preço · MA200 · P.Justo · Upside · DY · Div/ano · ROE · P/L · Score · Sinal
- Ordenável por qualquer coluna
- Filtro por sinal (BUY/HOLD/SELL) e por estratégia (DIVIDENDO/GROWTH)
- Linha colorida por sinal

**Seção 4 — Botão "Atualizar agora"**
- Chama `POST /scan/run`
- Mostra spinner durante o scan (~30s)
- Atualiza a tabela ao terminar

### 6.3 Histórico de Score (`/dashboard/historico`)
- Input: selecionar ticker
- Gráfico de linha (Recharts): score no tempo (30/90/365 dias)
- Segundo gráfico: preço vs preço justo no tempo
- Tabela abaixo: série completa de snapshots

### 6.4 Carteira (`/dashboard/carteira`)
**Resumo**
- Cards: total investido · valor atual · lucro de capital · dividendos recebidos · retorno total

**Tabela de posições**
- Colunas: Ticker · Qtd · PM · Preço atual · Investido · Valor atual · Rent. capital · Dividendos · Retorno total
- Linha verde se positivo, vermelha se negativo

**Formulário — Adicionar posição**
- Campos: ticker, preço, quantidade, data, nota
- Validação: ticker deve existir na B3

**Formulário — Registrar dividendo**
- Campos: ticker, valor por ação, data pagamento

**Gráfico — Composição da carteira**
- Pizza: % de cada ativo no total investido
- Alerta visual se algum ativo > 30%

### 6.5 Backtest (`/dashboard/backtest`)
- Selector: ticker + período (1y/2y/5y)
- KPIs: Retorno · CAGR · Sharpe · Max Drawdown · Alpha · Win Rate
- Gráfico de área: capital da estratégia vs Buy & Hold ao longo do tempo
- Tabela de trades: data, tipo, preço, lucro, motivo

---

## 7. Agentes e Sub-agentes — Ordem de Execução

O Claude Code deve executar na seguinte ordem, **um agente por vez**, validando antes de avançar.

```
AGENTE 0 — Preparação do servidor
  Responsabilidade: configurar o VPS para receber o projeto
  
  Tarefas:
  1. Criar banco PostgreSQL: createdb dividendo_bot
  2. Criar usuário PostgreSQL: dividendo_bot_user com senha
  3. Executar migrations (criar tabelas + índices)
  4. Configurar variáveis de ambiente em /etc/environment ou .env
  5. Testar conexão: python -c "from backend.db import engine; print('OK')"
  
  Critério de aceite: conexão com banco funcionando


AGENTE 1 — Back-end: autenticação
  Responsabilidade: FastAPI rodando com login JWT

  Tarefas:
  1. Criar backend/main.py com FastAPI básico
  2. Criar backend/db.py com SQLAlchemy + PostgreSQL
  3. Criar models/user.py
  4. Criar routers/auth.py (POST /auth/login)
  5. Criar usuário inicial via script: python backend/create_user.py
  
  Critério de aceite:
    curl -X POST http://localhost:8001/auth/login \
      -d '{"username":"isaac","password":"..."}' \
      → retorna access_token


AGENTE 2 — Back-end: scan e snapshots
  Responsabilidade: /scan/* funcionando e salvando no banco

  Tarefas:
  1. Criar models/snapshot.py
  2. Criar routers/scan.py (GET /scan/latest, POST /scan/run, 
     GET /scan/historico/{ticker})
  3. Integrar core/ existente: scan_watchlist() → salva snapshots
  4. Criar scheduler.py com APScheduler (scan diário 7h00)
  
  Critério de aceite:
    POST /scan/run → 200 OK com resultados
    SELECT COUNT(*) FROM snapshots → > 0
    GET /scan/historico/PETR4 → série de dados


AGENTE 3 — Back-end: carteira
  Responsabilidade: /carteira/* funcionando

  Tarefas:
  1. Criar models/carteira.py (posicoes + dividendos_recebidos)
  2. Criar routers/carteira.py (todos os endpoints)
  3. Migrar dados do carteira.json existente para PostgreSQL
  
  Critério de aceite:
    POST /carteira/posicao → cria posição
    GET /carteira → retorna resumo com rentabilidade calculada


AGENTE 4 — Back-end: backtest
  Responsabilidade: /backtest/* funcionando com cache no banco

  Tarefas:
  1. Criar models/backtest.py
  2. Criar routers/backtest.py
  3. Cache: se resultado < 24h no banco, retorna do banco
  4. Se não: roda backtester.py e salva
  
  Critério de aceite:
    GET /backtest/PETR4?periodo=5y → resultado completo
    Segunda chamada deve ser instantânea (cache)


AGENTE 5 — Infra: systemd + Nginx
  Responsabilidade: API rodando como serviço no VPS

  Tarefas:
  1. Criar /etc/systemd/system/dividendo-bot-api.service
  2. Criar nginx/dividendo_bot.conf (proxy para porta 8001)
  3. Habilitar e iniciar o serviço
  4. Testar via IP externo
  
  Critério de aceite:
    curl http://191.252.217.250/api/scan/latest → 200 OK


AGENTE 6 — Front-end: setup e login
  Responsabilidade: Next.js rodando com tela de login

  Tarefas:
  1. npx create-next-app@14 frontend --typescript --tailwind --app
  2. Instalar: shadcn/ui, recharts, axios
  3. Criar /login com formulário
  4. Implementar auth: POST /auth/login → salva token em cookie
  5. Middleware Next.js: rotas protegidas redirecionam para /login

  Critério de aceite:
    Abre http://191.252.217.250:3002/login
    Login com credenciais corretas → redireciona para /dashboard
    Login com credenciais erradas → mensagem de erro


AGENTE 7 — Front-end: dashboard e tabela de scan
  Responsabilidade: tela principal funcionando

  Tarefas:
  1. Criar /dashboard/page.tsx
  2. Componente KPICards (BUY/HOLD/SELL/última atualização)
  3. Componente Top5Cards
  4. Componente ScanTable (ordenável, filtrável)
  5. Botão "Atualizar agora" com spinner

  Critério de aceite:
    Dashboard carrega com dados reais do banco
    Filtro por BUY funciona
    Botão atualizar dispara scan e recarrega tabela


AGENTE 8 — Front-end: histórico de score
  Responsabilidade: gráficos de evolução no tempo

  Tarefas:
  1. Criar /dashboard/historico/page.tsx
  2. Selector de ticker
  3. Gráfico Recharts: score no tempo
  4. Gráfico: preço vs preço justo
  5. Tabela com série completa

  Critério de aceite:
    Seleciona PETR4 → gráfico aparece com pelo menos 7 dias de dados


AGENTE 9 — Front-end: carteira
  Responsabilidade: gestão de carteira completa

  Tarefas:
  1. Criar /dashboard/carteira/page.tsx
  2. Cards de resumo (total investido, rentabilidade, etc.)
  3. Tabela de posições com cores
  4. Formulário adicionar posição
  5. Formulário registrar dividendo
  6. Gráfico pizza de composição

  Critério de aceite:
    Adiciona PETR4 100 @ R$38,20 → aparece na tabela
    Registra dividendo R$0,85 → total de dividendos atualiza
    Gráfico pizza renderiza


AGENTE 10 — Front-end: backtest
  Responsabilidade: visualização de backtest

  Tarefas:
  1. Criar /dashboard/backtest/page.tsx
  2. Selector ticker + período
  3. KPIs: retorno, CAGR, Sharpe, drawdown, alpha, win rate
  4. Gráfico de área: capital estratégia vs B&H
  5. Tabela de trades

  Critério de aceite:
    Seleciona PETR4 5y → gráfico renderiza
    Segunda consulta é instantânea (cache do banco)


AGENTE 11 — Front-end: Nginx + PM2 + SSL
  Responsabilidade: front-end no ar via HTTPS

  Tarefas:
  1. Build Next.js: npm run build
  2. PM2: pm2 start npm --name "dividendo-bot-front" -- start
  3. Atualizar nginx para servir o front na porta 3002
  4. Certbot: certificado SSL para o domínio (se tiver) ou IP

  Critério de aceite:
    https://[domínio ou IP] → dashboard carrega via HTTPS


AGENTE 12 — CI/CD
  Responsabilidade: deploy automático no push

  Tarefas:
  1. Criar .github/workflows/deploy.yml
  2. On push main:
     - SSH no VPS
     - git pull
     - pip install requirements
     - npm run build (frontend)
     - systemctl restart dividendo-bot-api
     - pm2 restart dividendo-bot-front
  3. Configurar secrets no GitHub: VPS_HOST, VPS_USER, VPS_KEY

  Critério de aceite:
    Push em main → GitHub Actions verde → mudança aparece no ar


AGENTE 13 — Testes
  Responsabilidade: cobertura mínima de testes

  Tarefas:
  
  Unit tests (tests/unit/):
    test_score.py       → calcular_score() retorna 0-10
    test_valuation.py   → preço justo dentro de sanity bounds
    test_validators.py  → sanity checks rejeitam valores absurdos
    test_sinal.py       → BUY exige upside >= 10%

  Integration tests (tests/integration/):
    test_api_scan.py    → POST /scan/run → 200 + dados no banco
    test_api_carteira.py→ CRUD completo de posições
    test_api_backtest.py→ resultado + cache funcionando

  E2E tests (tests/e2e/):
    test_login.py       → login válido + inválido (Playwright)
    test_dashboard.py   → tabela carrega, filtro funciona
    test_carteira_e2e.py→ adicionar posição via UI

  Critério de aceite:
    pytest tests/unit/   → 100% passa
    pytest tests/integration/ → 100% passa
    playwright test      → todos E2E verdes


AGENTE 14 — QA final
  Responsabilidade: smoke test completo antes de considerar entregue

  Checklist:
  [ ] Login funciona
  [ ] Scan ao vivo roda e salva no banco
  [ ] Scan agendado (7h) está registrado no APScheduler
  [ ] Tabela ordena e filtra
  [ ] Top 5 aparece correto
  [ ] Histórico de score mostra gráfico com dados reais
  [ ] Adicionar posição → aparece na carteira com rentabilidade
  [ ] Registrar dividendo → total atualiza
  [ ] Gráfico de composição renderiza
  [ ] Backtest PETR4 roda e mostra gráfico
  [ ] Segunda consulta backtest é instantânea
  [ ] Push no GitHub → deploy automático funciona
  [ ] Acesso via HTTPS (ou HTTP se sem domínio)
  [ ] Nenhum None visível na tabela de scan
  [ ] Nenhuma chave de API ou senha no código (tudo em .env)
```

---

## 8. Variáveis de Ambiente (.env)

```bash
# Banco
DATABASE_URL=postgresql://dividendo_bot_user:SENHA@localhost:5432/dividendo_bot

# Auth JWT
JWT_SECRET=gera_uma_string_aleatoria_longa_aqui
JWT_EXPIRE_MINUTES=1440   # 24 horas

# Usuário inicial (só pra criação via script)
ADMIN_USERNAME=isaac
ADMIN_PASSWORD=sua_senha_aqui

# Dados externos
BRAPI_TOKEN=                # vazio = usa token demo com limite

# App
SCAN_HORA=7                 # hora do scan automático
AMBIENTE=production
```

---

## 9. Regras para o Claude Code (incluir no início de cada agente)

```
Regras desta sessão:
- Leia todos os arquivos relevantes ANTES de escrever código
- Teste cada entrega antes de avançar para a próxima
- Nunca quebre interfaces existentes — estenda, não substitua
- O código em core/ nunca é modificado — só consumido
- Todas as senhas e tokens em .env, nunca hardcoded
- Cada agente termina com um teste de aceitação explícito
- Commit separado ao final de cada agente
- Se travar em algo por mais de 15 minutos, pare e descreva 
  o problema em vez de tentar workarounds criativos
```

---

## 10. O que NÃO está no escopo (decisão explícita)

- ❌ Execução automática de ordens (sem integração com corretora)
- ❌ Alertas Telegram (fase futura)
- ❌ Machine Learning (decisão de arquitetura — modelo fatorial é mais robusto)
- ❌ Universo B3 completo (~400 tickers) — watchlist fixa por enquanto
- ❌ RSI, Bollinger Bands, indicadores técnicos de curto prazo
- ❌ App mobile nativo

---

## 11. Sequência de Execução no Claude Code

```
Sessão 1: Agentes 0, 1, 2     → banco + API core rodando
Sessão 2: Agentes 3, 4        → carteira + backtest na API
Sessão 3: Agente 5            → infra VPS (systemd + Nginx)
Sessão 4: Agentes 6, 7        → front login + dashboard
Sessão 5: Agentes 8, 9, 10    → front histórico + carteira + backtest
Sessão 6: Agentes 11, 12      → deploy + CI/CD
Sessão 7: Agentes 13, 14      → testes + QA final
```

Cada sessão começa com:  
`"Leia o PRD.md e o dividend_bot.md antes de qualquer coisa."`

---

*PRD gerado em 02/07/2026 — versão 1.0*
