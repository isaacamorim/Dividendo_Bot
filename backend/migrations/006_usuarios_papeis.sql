-- 006_usuarios_papeis.sql — papéis e status nos usuários (espelha o Tradeon).
-- Papéis: admin > gestor > operador > leitor. Dados ainda compartilhados
-- (separar carteira por usuário é fase futura).
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'leitor'
       CHECK (role IN ('admin','gestor','operador','leitor')),
  ADD COLUMN IF NOT EXISTS active BOOLEAN NOT NULL DEFAULT TRUE,
  ADD COLUMN IF NOT EXISTS last_login TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS created_by VARCHAR(50);

-- O usuário existente (isaac) vira admin.
UPDATE users SET role='admin' WHERE username='isaac';
