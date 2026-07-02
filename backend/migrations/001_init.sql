-- backend/migrations/001_init.sql
-- Schema inicial do Dividend Bot (PRD seção 4). Idempotente (IF NOT EXISTS).
-- Compatível com PostgreSQL 12+ (VPS roda 12.22).

-- Usuários (autenticação simples)
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Snapshot diário de cada ativo
CREATE TABLE IF NOT EXISTS snapshots (
    id           SERIAL PRIMARY KEY,
    ticker       VARCHAR(10) NOT NULL,
    data         DATE NOT NULL,
    preco        NUMERIC(10,2),
    preco_justo  NUMERIC(10,2),
    upside       NUMERIC(6,2),
    dy           NUMERIC(6,2),
    roe          NUMERIC(6,2),
    pl           NUMERIC(8,2),
    score        NUMERIC(4,2),
    sinal        VARCHAR(10),
    estrategia   VARCHAR(15),
    setor_perfil VARCHAR(30),
    div_estimado NUMERIC(8,2),
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (ticker, data)           -- um snapshot por ativo por dia
);

-- Posições da carteira
CREATE TABLE IF NOT EXISTS posicoes (
    id           SERIAL PRIMARY KEY,
    ticker       VARCHAR(10) NOT NULL,
    data_compra  DATE NOT NULL,
    preco_compra NUMERIC(10,2) NOT NULL,
    quantidade   INTEGER NOT NULL,
    nota         TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Dividendos recebidos
CREATE TABLE IF NOT EXISTS dividendos_recebidos (
    id             SERIAL PRIMARY KEY,
    ticker         VARCHAR(10) NOT NULL,
    data_pagamento DATE NOT NULL,
    valor_por_acao NUMERIC(8,4) NOT NULL,
    quantidade     INTEGER NOT NULL,
    total          NUMERIC(10,2) NOT NULL,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- Resultados de backtest (cache)
CREATE TABLE IF NOT EXISTS backtest_runs (
    id           SERIAL PRIMARY KEY,
    ticker       VARCHAR(10) NOT NULL,
    periodo      VARCHAR(10) NOT NULL,
    retorno_pct  NUMERIC(8,2),
    cagr_pct     NUMERIC(8,2),
    sharpe       NUMERIC(6,3),
    max_drawdown NUMERIC(8,2),
    alpha_pct    NUMERIC(8,2),
    win_rate_pct NUMERIC(6,2),
    n_trades     INTEGER,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (ticker, periodo)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_snapshots_ticker_data ON snapshots(ticker, data DESC);
CREATE INDEX IF NOT EXISTS idx_posicoes_ticker        ON posicoes(ticker);
CREATE INDEX IF NOT EXISTS idx_dividendos_ticker      ON dividendos_recebidos(ticker);
