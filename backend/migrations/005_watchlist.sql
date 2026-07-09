-- 005_watchlist.sql — watchlist gerenciável pela UI (fonte da verdade do scan).
-- O scanner passa a ler os tickers ativos daqui; settings.WATCHLIST_COMPLETA
-- vira fallback (se a tabela estiver vazia).
CREATE TABLE IF NOT EXISTS watchlist (
  id            SERIAL PRIMARY KEY,
  ticker        VARCHAR(10) UNIQUE NOT NULL,
  nome          VARCHAR(100),
  setor         VARCHAR(50),
  setor_perfil  VARCHAR(30),
  ativo         BOOLEAN DEFAULT TRUE,
  adicionado_em TIMESTAMPTZ DEFAULT NOW(),
  nota          TEXT
);

-- Seed com os 28 ativos atuais (20 ações + 8 FIIs). Idempotente.
INSERT INTO watchlist (ticker, setor_perfil) VALUES
  ('BBAS3',  'Bancos/Fin.'),
  ('ITUB4',  'Bancos/Fin.'),
  ('BBDC4',  'Bancos/Fin.'),
  ('TAEE11', 'Energia'),
  ('ISAE4',  'Energia'),
  ('CMIG4',  'Energia'),
  ('CPLE3',  'Energia'),
  ('EGIE3',  'Energia'),
  ('PETR4',  'Petróleo/Gás'),
  ('VALE3',  'Commodities'),
  ('VIVT3',  'Telecom/Mídia'),
  ('WEGE3',  'Industrial/Growth'),
  ('TOTS3',  'Tecnologia'),
  ('RADL3',  'Saúde'),
  ('RDOR3',  'Saúde'),
  ('ABEV3',  'Consumo'),
  ('LREN3',  'Consumo'),
  ('CXSE3',  'Seguros'),
  ('SUZB3',  'Papel/Celulose'),
  ('MULT3',  'Shopping'),
  ('HGLG11', 'FII'),
  ('XPML11', 'FII'),
  ('MXRF11', 'FII'),
  ('KNRI11', 'FII'),
  ('VISC11', 'FII'),
  ('KNIP11', 'FII'),
  ('BRCO11', 'FII'),
  ('RBRF11', 'FII')
ON CONFLICT (ticker) DO NOTHING;
