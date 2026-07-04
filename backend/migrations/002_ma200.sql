-- backend/migrations/002_ma200.sql
-- Adiciona MA200 (média móvel de 200 períodos) ao snapshot. Idempotente.

ALTER TABLE snapshots ADD COLUMN IF NOT EXISTS ma200 NUMERIC(10,2);
