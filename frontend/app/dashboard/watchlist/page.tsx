"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { WatchlistAtivo, WatchlistResponse, WatchlistValidacao } from "@/types";

const API = process.env.NEXT_PUBLIC_API_URL || "";

type Filtro = "TODOS" | "ACOES" | "FIIS" | "INATIVOS";

const dataFmt = (iso: string | null) => {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
};

export default function WatchlistPage() {
  const router = useRouter();
  const [ativos, setAtivos] = useState<WatchlistAtivo[]>([]);
  const [perfis, setPerfis] = useState<string[]>([]);
  const [carregando, setCarregando] = useState(true);

  // Seção adicionar
  const [input, setInput] = useState("");
  const [validando, setValidando] = useState(false);
  const [validacao, setValidacao] = useState<WatchlistValidacao | null>(null);
  const [setorSel, setSetorSel] = useState("");
  const [nota, setNota] = useState("");
  const [adicionando, setAdicionando] = useState(false);
  const [msg, setMsg] = useState<{ tipo: "ok" | "warn" | "erro"; texto: string } | null>(null);

  // Filtro e edição
  const [filtro, setFiltro] = useState<Filtro>("TODOS");
  const [editando, setEditando] = useState<string | null>(null);
  const [editSetor, setEditSetor] = useState("");

  const carregar = useCallback(async () => {
    try {
      const resp = await fetch(`${API}/watchlist`, { credentials: "include" });
      if (resp.status === 401) {
        router.push("/login");
        return;
      }
      const data: WatchlistResponse = await resp.json();
      setAtivos(data.ativos);
      setPerfis(data.perfis || []);
    } catch {
      // silencioso
    } finally {
      setCarregando(false);
    }
  }, [router]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  async function verificar() {
    const tk = input.trim().toUpperCase().replace(".SA", "");
    if (!tk) return;
    setValidando(true);
    setValidacao(null);
    setMsg(null);
    try {
      const resp = await fetch(`${API}/watchlist/validar/${tk}`, { credentials: "include" });
      const v: WatchlistValidacao = await resp.json();
      setValidacao(v);
      if (v.valido) {
        const detectado = v.setor_perfil || "";
        setSetorSel(detectado);
        if (!v.setor_detectado) {
          setMsg({
            tipo: "warn",
            texto: `⚠️ ${v.ticker} válido, mas sem dados de setor — selecione manualmente.`,
          });
        } else {
          setMsg({
            tipo: "ok",
            texto: `✅ ${v.ticker}${v.nome ? ` — ${v.nome}` : ""} · Setor detectado: ${detectado}`,
          });
        }
      } else {
        setMsg({ tipo: "erro", texto: `❌ Ticker não encontrado na B3` });
      }
    } catch {
      setMsg({ tipo: "erro", texto: "Erro ao validar o ticker." });
    } finally {
      setValidando(false);
    }
  }

  async function adicionar() {
    if (!validacao?.valido) return;
    setAdicionando(true);
    try {
      const resp = await fetch(`${API}/watchlist`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker: validacao.ticker,
          setor_perfil: setorSel || undefined,
          nota: nota || undefined,
        }),
      });
      if (!resp.ok) {
        const e = await resp.json().catch(() => ({}));
        setMsg({ tipo: "erro", texto: e.detail || "Falha ao adicionar." });
        return;
      }
      setMsg({
        tipo: "ok",
        texto: `✅ ${validacao.ticker} adicionado! Será incluído no próximo scan (amanhã 7h) ou clique em Atualizar agora no dashboard.`,
      });
      setInput("");
      setValidacao(null);
      setNota("");
      setSetorSel("");
      await carregar();
    } catch {
      setMsg({ tipo: "erro", texto: "Erro de rede ao adicionar." });
    } finally {
      setAdicionando(false);
    }
  }

  async function salvarEdicao(ticker: string) {
    try {
      await fetch(`${API}/watchlist/${ticker}`, {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ setor_perfil: editSetor }),
      });
      setEditando(null);
      await carregar();
    } catch {
      // silencioso
    }
  }

  async function remover(ticker: string) {
    if (!confirm(`Remover ${ticker} da watchlist? (soft delete — o histórico é preservado)`)) return;
    try {
      await fetch(`${API}/watchlist/${ticker}`, { method: "DELETE", credentials: "include" });
      await carregar();
    } catch {
      // silencioso
    }
  }

  const filtrados = ativos.filter((a) => {
    if (filtro === "INATIVOS") return !a.ativo;
    if (!a.ativo) return false;
    if (filtro === "FIIS") return a.setor_perfil === "FII";
    if (filtro === "ACOES") return a.setor_perfil !== "FII";
    return true;
  });

  const corMsg =
    msg?.tipo === "ok" ? "text-emerald-400" : msg?.tipo === "warn" ? "text-amber-400" : "text-red-400";

  return (
    <main className="mx-auto max-w-5xl px-4 py-6">
      <header className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-bold">⚙️ Gestão da Watchlist</h1>
        <Link
          href="/dashboard"
          className="rounded-lg bg-zinc-800 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-700"
        >
          ← Dashboard
        </Link>
      </header>

      {/* SEÇÃO 1 — Adicionar ativo */}
      <section className="mb-8 rounded-xl border border-zinc-800 bg-zinc-900 p-4">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-400">
          Adicionar ativo
        </h2>
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && verificar()}
            placeholder="Código do ativo (ex: PETR4 ou PETR4.SA)"
            className="min-h-[44px] flex-1 rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm outline-none focus:border-emerald-500 sm:min-h-0"
          />
          <button
            onClick={verificar}
            disabled={validando || !input.trim()}
            className="min-h-[44px] rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-900 hover:bg-white disabled:opacity-50 sm:min-h-0"
          >
            {validando ? "Verificando..." : "Verificar"}
          </button>
        </div>

        {msg && <p className={`mt-3 text-sm ${corMsg}`}>{msg.texto}</p>}

        {validacao?.valido && (
          <div className="mt-4 space-y-3 rounded-lg border border-zinc-800 bg-zinc-950 p-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs text-zinc-400">Setor / Perfil</label>
                <select
                  value={setorSel}
                  onChange={(e) => setSetorSel(e.target.value)}
                  className="min-h-[44px] w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm outline-none focus:border-emerald-500 sm:min-h-0"
                >
                  {setorSel && !perfis.includes(setorSel) && (
                    <option value={setorSel}>{setorSel}</option>
                  )}
                  {perfis.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs text-zinc-400">Nota (opcional)</label>
                <input
                  value={nota}
                  onChange={(e) => setNota(e.target.value)}
                  placeholder="Ex: tese de dividendos"
                  className="min-h-[44px] w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm outline-none focus:border-emerald-500 sm:min-h-0"
                />
              </div>
            </div>
            <button
              onClick={adicionar}
              disabled={adicionando}
              className="min-h-[44px] rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50 sm:min-h-0"
            >
              {adicionando ? "Adicionando..." : "Adicionar à watchlist"}
            </button>
          </div>
        )}
      </section>

      {/* SEÇÃO 2 — Ativos monitorados */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-400">
            Ativos monitorados
          </h2>
          <div className="flex gap-2">
            {(["TODOS", "ACOES", "FIIS", "INATIVOS"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFiltro(f)}
                className={`min-h-[44px] rounded-lg px-3 py-1 text-xs sm:min-h-0 ${
                  filtro === f ? "bg-zinc-100 text-zinc-900" : "bg-zinc-800 text-zinc-300"
                }`}
              >
                {f === "ACOES" ? "Ações" : f === "FIIS" ? "FIIs" : f === "INATIVOS" ? "Inativos" : "Todos"}
              </button>
            ))}
          </div>
        </div>

        {carregando ? (
          <div className="animate-pulse text-zinc-500">Carregando...</div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-zinc-800">
            <table className="w-full text-sm">
              <thead className="bg-zinc-900 text-zinc-400">
                <tr>
                  {["Ticker", "Nome", "Setor/Perfil", "Adicionado", "Nota", "Ações"].map((h) => (
                    <th key={h} className="px-3 py-2 text-left">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtrados.map((a) => (
                  <tr
                    key={a.ticker}
                    className={`border-t border-zinc-800 ${a.ativo ? "" : "opacity-50"}`}
                  >
                    <td className="px-3 py-2 font-medium">{a.ticker}</td>
                    <td className="px-3 py-2 text-zinc-400">{a.nome || "—"}</td>
                    <td className="px-3 py-2">
                      {editando === a.ticker ? (
                        <select
                          value={editSetor}
                          onChange={(e) => setEditSetor(e.target.value)}
                          className="rounded border border-zinc-700 bg-zinc-800 px-2 py-1 text-xs"
                        >
                          {editSetor && !perfis.includes(editSetor) && (
                            <option value={editSetor}>{editSetor}</option>
                          )}
                          {perfis.map((p) => (
                            <option key={p} value={p}>
                              {p}
                            </option>
                          ))}
                        </select>
                      ) : (
                        a.setor_perfil || "—"
                      )}
                    </td>
                    <td className="px-3 py-2 text-zinc-400">{dataFmt(a.adicionado_em)}</td>
                    <td className="px-3 py-2 text-zinc-400" title={a.nota || ""}>
                      {a.nota ? (a.nota.length > 20 ? a.nota.slice(0, 20) + "…" : a.nota) : "—"}
                    </td>
                    <td className="px-3 py-2">
                      {editando === a.ticker ? (
                        <div className="flex gap-1">
                          <button
                            onClick={() => salvarEdicao(a.ticker)}
                            className="rounded bg-emerald-600 px-2 py-1 text-xs text-white hover:bg-emerald-500"
                          >
                            Salvar
                          </button>
                          <button
                            onClick={() => setEditando(null)}
                            className="rounded bg-zinc-800 px-2 py-1 text-xs text-zinc-300 hover:bg-zinc-700"
                          >
                            Cancelar
                          </button>
                        </div>
                      ) : (
                        <div className="flex gap-2">
                          <button
                            onClick={() => {
                              setEditando(a.ticker);
                              setEditSetor(a.setor_perfil || "");
                            }}
                            title="Editar setor/perfil"
                            className="rounded bg-zinc-800 px-2 py-1 text-xs text-zinc-300 hover:bg-zinc-700"
                          >
                            ✏️
                          </button>
                          {a.ativo && (
                            <button
                              onClick={() => remover(a.ticker)}
                              title="Remover"
                              className="rounded bg-zinc-800 px-2 py-1 text-xs text-red-400 hover:bg-zinc-700"
                            >
                              🗑️
                            </button>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
                {filtrados.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-3 py-8 text-center text-zinc-500">
                      Nenhum ativo neste filtro.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
