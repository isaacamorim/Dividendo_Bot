-- 003_snapshot_campos.sql — campos fundamentais extras no snapshot diário.
-- divida_ebitda / payout / eps_growth ja vem de get_fundamentos (pontos %).
ALTER TABLE snapshots
  ADD COLUMN IF NOT EXISTS divida_ebitda NUMERIC(6,2),
  ADD COLUMN IF NOT EXISTS payout        NUMERIC(6,2),
  ADD COLUMN IF NOT EXISTS eps_growth    NUMERIC(8,2);
