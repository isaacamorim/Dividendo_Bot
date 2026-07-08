-- 004_alertas.sql — alertas do painel (sino no dashboard).
-- Gerados pelo scanner: NOVO_BUY / SAIU_BUY (mudanca de sinal vs dia anterior)
-- e STOP_LOSS / TAKE_PROFIT (posicoes da carteira).
CREATE TABLE IF NOT EXISTS alertas (
  id         SERIAL PRIMARY KEY,
  ticker     VARCHAR(10) NOT NULL,
  tipo       VARCHAR(30) NOT NULL,
  mensagem   TEXT NOT NULL,
  score      NUMERIC(4,2),
  sinal      VARCHAR(10),
  lido       BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alertas_lido ON alertas (lido);
CREATE INDEX IF NOT EXISTS idx_alertas_created ON alertas (created_at DESC);
