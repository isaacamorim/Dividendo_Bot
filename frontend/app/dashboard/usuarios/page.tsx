"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Me, UsuarioItem, UsuariosResponse } from "@/types";

const API = process.env.NEXT_PUBLIC_API_URL || "";

const ROLE_LABEL: Record<string, string> = {
  admin: "Admin",
  gestor: "Gestor",
  operador: "Operador",
  leitor: "Leitor",
};

const ROLE_DESC: Record<string, string> = {
  admin: "Controle total: gerencia usuários e usa tudo.",
  gestor: "Cria e gerencia operador/leitor. Usa tudo.",
  operador: "Usa tudo (scan, carteira, watchlist, GPT). Não gerencia usuários.",
  leitor: "Só visualiza o painel — não edita nem gerencia.",
};

function RoleBadge({ role }: { role: string }) {
  const cor =
    {
      admin: "bg-violet-900/40 text-violet-300 border-violet-700/50",
      gestor: "bg-blue-900/40 text-blue-300 border-blue-700/50",
      operador: "bg-amber-900/40 text-amber-300 border-amber-700/50",
      leitor: "bg-zinc-800 text-zinc-400 border-zinc-700",
    }[role] || "bg-zinc-800 text-zinc-400 border-zinc-700";
  return (
    <span className={`rounded-full border px-2 py-0.5 text-xs font-medium ${cor}`}>
      {ROLE_LABEL[role] || role}
    </span>
  );
}

export default function UsuariosPage() {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [ready, setReady] = useState(false);
  const [users, setUsers] = useState<UsuarioItem[]>([]);
  const [assignable, setAssignable] = useState<string[]>([]);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const [nu, setNu] = useState("");
  const [np, setNp] = useState("");
  const [nr, setNr] = useState("leitor");
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    const r = await fetch(`${API}/users`, { credentials: "include" })
      .then((r) => r.json())
      .catch(() => null);
    if (r && r.ok) {
      setUsers(r.users as UsuarioItem[]);
      setAssignable((r as UsuariosResponse).assignable || []);
    }
  }, []);

  useEffect(() => {
    fetch(`${API}/auth/me`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: Me) => {
        if (d.role !== "admin" && d.role !== "gestor") {
          router.replace("/dashboard");
          return;
        }
        setMe(d);
        setReady(true);
      })
      .catch(() => router.replace("/login"));
  }, [router]);

  useEffect(() => {
    if (ready) load();
  }, [ready, load]);

  function flash(ok: boolean, text: string) {
    setMsg({ ok, text });
    setTimeout(() => setMsg(null), 4000);
  }

  async function createUser() {
    setCreating(true);
    const res = await fetch(`${API}/users`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: nu, password: np, role: nr }),
    });
    const d = await res.json().catch(() => ({}));
    setCreating(false);
    if (!res.ok || !d.ok) {
      flash(false, d.detail || "Falha ao criar usuário.");
      return;
    }
    flash(true, `Usuário "${d.user.username}" criado.`);
    setNu("");
    setNp("");
    setNr("leitor");
    load();
  }

  async function patchUser(id: number, body: Record<string, unknown>, okText: string) {
    const res = await fetch(`${API}/users/${id}`, {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const d = await res.json().catch(() => ({}));
    if (!res.ok || !d.ok) {
      flash(false, d.detail || "Falha ao atualizar.");
      return;
    }
    flash(true, okText);
    load();
  }

  async function resetPassword(u: UsuarioItem) {
    const pw = window.prompt(`Nova senha para "${u.username}" (mín. 6):`);
    if (pw == null) return;
    if (pw.length < 6) {
      flash(false, "Senha muito curta.");
      return;
    }
    patchUser(u.id, { password: pw }, "Senha redefinida.");
  }

  async function removeUser(u: UsuarioItem) {
    if (!window.confirm(`Excluir o usuário "${u.username}"? Não dá pra desfazer.`)) return;
    const res = await fetch(`${API}/users/${u.id}`, {
      method: "DELETE",
      credentials: "include",
    });
    const d = await res.json().catch(() => ({}));
    if (!res.ok || !d.ok) {
      flash(false, d.detail || "Falha ao excluir.");
      return;
    }
    flash(true, `Usuário "${u.username}" excluído.`);
    load();
  }

  // gestor não pode agir sobre admin/gestor
  function canEdit(u: UsuarioItem) {
    if (me?.role === "admin") return true;
    return u.role === "operador" || u.role === "leitor";
  }

  if (!ready || !me) return null;

  return (
    <main className="mx-auto max-w-3xl px-4 py-6">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold">👥 Usuários</h1>
          <p className="mt-0.5 text-xs text-zinc-500">
            Logado como <span className="text-zinc-300">{me.username}</span> ·{" "}
            <RoleBadge role={me.role} />
          </p>
        </div>
        <Link
          href="/dashboard"
          className="rounded-lg bg-zinc-800 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-700"
        >
          ← Dashboard
        </Link>
      </header>

      {msg && (
        <div
          className={`mb-4 rounded-lg border px-3 py-2 text-xs ${
            msg.ok
              ? "border-emerald-700/40 bg-emerald-900/20 text-emerald-400"
              : "border-rose-700/40 bg-rose-900/20 text-rose-400"
          }`}
        >
          {msg.text}
        </div>
      )}

      {/* Criar usuário */}
      <div className="mb-6 rounded-2xl border border-zinc-800 bg-zinc-900/40 p-4">
        <h2 className="mb-3 text-sm font-semibold text-zinc-300">Novo usuário</h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <input
            value={nu}
            onChange={(e) => setNu(e.target.value)}
            placeholder="usuário"
            autoCapitalize="none"
            className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-emerald-500"
          />
          <input
            value={np}
            onChange={(e) => setNp(e.target.value)}
            type="password"
            placeholder="senha (mín. 6)"
            className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-emerald-500"
          />
          <select
            value={nr}
            onChange={(e) => setNr(e.target.value)}
            className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-emerald-500"
          >
            {assignable.map((r) => (
              <option key={r} value={r}>
                {ROLE_LABEL[r] || r}
              </option>
            ))}
          </select>
        </div>
        <p className="mt-2 text-xs text-zinc-600">{ROLE_DESC[nr]}</p>
        <button
          onClick={createUser}
          disabled={creating || !nu || !np}
          className="mt-3 rounded-lg bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-600 disabled:bg-zinc-800 disabled:text-zinc-600"
        >
          {creating ? "Criando…" : "Criar usuário"}
        </button>
      </div>

      {/* Lista */}
      <div className="overflow-x-auto rounded-2xl border border-zinc-800 bg-zinc-900/40">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 text-left text-xs uppercase tracking-wider text-zinc-500">
              <th className="px-4 py-2.5">Usuário</th>
              <th className="px-4 py-2.5">Perfil</th>
              <th className="px-4 py-2.5">Status</th>
              <th className="px-4 py-2.5 text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-zinc-800/40">
                <td className="px-4 py-2.5">
                  <span className="text-zinc-200">{u.username}</span>
                  {u.username === me.username && (
                    <span className="ml-1 text-xs text-zinc-600">(você)</span>
                  )}
                </td>
                <td className="px-4 py-2.5">
                  {canEdit(u) && u.username !== me.username ? (
                    <select
                      value={u.role}
                      onChange={(e) => patchUser(u.id, { role: e.target.value }, "Perfil atualizado.")}
                      className="rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1 text-xs outline-none focus:border-emerald-500"
                    >
                      {assignable.map((r) => (
                        <option key={r} value={r}>
                          {ROLE_LABEL[r] || r}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <RoleBadge role={u.role} />
                  )}
                </td>
                <td className="px-4 py-2.5">
                  {u.active ? (
                    <span className="text-xs text-emerald-400">● ativo</span>
                  ) : (
                    <span className="text-xs text-zinc-600">● inativo</span>
                  )}
                </td>
                <td className="space-x-2 whitespace-nowrap px-4 py-2.5 text-right">
                  {canEdit(u) && u.username !== me.username && (
                    <>
                      <button
                        onClick={() =>
                          patchUser(u.id, { active: !u.active }, u.active ? "Desativado." : "Ativado.")
                        }
                        className="text-xs text-zinc-400 hover:text-amber-400"
                      >
                        {u.active ? "Desativar" : "Ativar"}
                      </button>
                      <button
                        onClick={() => resetPassword(u)}
                        className="text-xs text-zinc-400 hover:text-blue-400"
                      >
                        Redefinir senha
                      </button>
                      {me.role === "admin" && (
                        <button
                          onClick={() => removeUser(u)}
                          className="text-xs text-zinc-400 hover:text-rose-400"
                        >
                          Excluir
                        </button>
                      )}
                    </>
                  )}
                </td>
              </tr>
            ))}
            {!users.length && (
              <tr>
                <td colSpan={4} className="py-6 text-center text-xs text-zinc-600">
                  Nenhum usuário
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <p className="mt-6 text-center text-xs text-zinc-700">
        As permissões são validadas no servidor. Perfis: Admin · Gestor · Operador · Leitor.
      </p>
    </main>
  );
}
