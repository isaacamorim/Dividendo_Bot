"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Me, ScanLatest } from "@/types";
import { useAuth } from "@/hooks/useAuth";
import KPICards from "@/components/KPICards";
import Top5Cards from "@/components/Top5Cards";
import ScanTable from "@/components/ScanTable";
import AlertaBadge from "@/components/AlertaBadge";

const API = process.env.NEXT_PUBLIC_API_URL || "";

// Item do drawer mobile — alvo de toque >= 44px
const menuItemCls =
  "flex min-h-[44px] items-center rounded-lg bg-zinc-800 px-3 text-sm text-zinc-300 hover:bg-zinc-700";

export default function Dashboard() {
  const router = useRouter();
  const { logout } = useAuth();
  const [dados, setDados] = useState<ScanLatest | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [escaneando, setEscaneando] = useState(false);
  const [me, setMe] = useState<Me | null>(null);
  const [menuAberto, setMenuAberto] = useState(false);

  const carregar = useCallback(async () => {
    try {
      const resp = await fetch(`${API}/scan/latest`, { credentials: "include" });
      if (resp.status === 401) {
        router.push("/login");
        return;
      }
      setDados(await resp.json());
    } catch {
      // silencioso — mantém o estado anterior
    } finally {
      setCarregando(false);
    }
  }, [router]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  useEffect(() => {
    fetch(`${API}/auth/me`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setMe(d))
      .catch(() => {});
  }, []);

  const podeEditar = me ? me.role !== "leitor" : true;
  const podeGerirUsuarios = me?.role === "admin" || me?.role === "gestor";

  async function atualizar() {
    setEscaneando(true);
    try {
      const resp = await fetch(`${API}/scan/run`, {
        method: "POST",
        credentials: "include",
      });
      if (resp.status === 401) {
        router.push("/login");
        return;
      }
      await carregar();
    } catch {
      // silencioso
    } finally {
      setEscaneando(false);
    }
  }

  const cont = { buy: 0, hold: 0, sell: 0 };
  dados?.resultados.forEach((r) => {
    if (r.sinal === "BUY") cont.buy++;
    else if (r.sinal === "SELL") cont.sell++;
    else cont.hold++;
  });

  return (
    <main className="mx-auto max-w-6xl px-4 py-6">
      <header className="mb-6 flex items-center justify-between gap-2">
        <h1 className="min-w-0 truncate text-lg font-bold sm:text-xl">
          📊 Dividend Bot B3 — B3 Scanner
        </h1>
        <div className="flex shrink-0 items-center gap-2">
          <AlertaBadge />
          {/* Navegação desktop (lg+) — inalterada */}
          <nav className="hidden items-center gap-2 lg:flex">
            <Link
              href="/dashboard/historico"
              className="rounded-lg bg-zinc-800 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-700"
            >
              📈 Ver histórico
            </Link>
            <Link
              href="/dashboard/carteira"
              className="rounded-lg bg-zinc-800 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-700"
            >
              💼 Minha Carteira
            </Link>
            <Link
              href="/dashboard/backtest"
              className="rounded-lg bg-zinc-800 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-700"
            >
              📈 Backtest
            </Link>
            <Link
              href="/dashboard/watchlist"
              className="rounded-lg bg-zinc-800 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-700"
            >
              ⚙️ Watchlist
            </Link>
            {podeGerirUsuarios && (
              <Link
                href="/dashboard/usuarios"
                className="rounded-lg bg-zinc-800 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-700"
              >
                👥 Usuários
              </Link>
            )}
            <a
              href="http://191.252.217.250:3002"
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg bg-zinc-800 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-700"
            >
              🤖 Tradeon ↗
            </a>
            {podeEditar && (
              <button
                onClick={atualizar}
                disabled={escaneando}
                className="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {escaneando ? "⏳ Escaneando... (~30s)" : "🔄 Atualizar agora"}
              </button>
            )}
            <button
              onClick={logout}
              className="rounded-lg bg-zinc-800 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-700"
            >
              Sair
            </button>
          </nav>
          {/* Hamburger mobile (<lg) */}
          <button
            onClick={() => setMenuAberto(true)}
            aria-label="Abrir menu"
            className="flex min-h-[44px] items-center rounded-lg bg-zinc-800 px-3 text-lg text-zinc-300 hover:bg-zinc-700 lg:hidden"
          >
            ☰
          </button>
        </div>
      </header>

      {/* Drawer de navegação mobile (<lg) */}
      {menuAberto && (
        <div className="fixed inset-0 z-50 flex justify-end lg:hidden">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setMenuAberto(false)}
            aria-hidden
          />
          <aside className="relative flex h-full w-72 max-w-[80vw] flex-col border-l border-zinc-800 bg-zinc-950 p-4 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <span className="text-sm font-semibold text-zinc-200">Menu</span>
              <button
                onClick={() => setMenuAberto(false)}
                className="flex min-h-[44px] items-center rounded-lg bg-zinc-800 px-3 text-sm text-zinc-300 hover:bg-zinc-700"
              >
                Fechar
              </button>
            </div>
            <nav className="flex flex-col gap-2">
              <Link href="/dashboard/historico" onClick={() => setMenuAberto(false)} className={menuItemCls}>
                📈 Ver histórico
              </Link>
              <Link href="/dashboard/carteira" onClick={() => setMenuAberto(false)} className={menuItemCls}>
                💼 Minha Carteira
              </Link>
              <Link href="/dashboard/backtest" onClick={() => setMenuAberto(false)} className={menuItemCls}>
                📈 Backtest
              </Link>
              <Link href="/dashboard/watchlist" onClick={() => setMenuAberto(false)} className={menuItemCls}>
                ⚙️ Watchlist
              </Link>
              {podeGerirUsuarios && (
                <Link href="/dashboard/usuarios" onClick={() => setMenuAberto(false)} className={menuItemCls}>
                  👥 Usuários
                </Link>
              )}
              <a
                href="http://191.252.217.250:3002"
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => setMenuAberto(false)}
                className={menuItemCls}
              >
                🤖 Tradeon ↗
              </a>
              {podeEditar && (
                <button
                  onClick={() => {
                    setMenuAberto(false);
                    atualizar();
                  }}
                  disabled={escaneando}
                  className="flex min-h-[44px] items-center justify-center rounded-lg bg-emerald-600 px-3 text-sm font-medium text-white hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {escaneando ? "⏳ Escaneando... (~30s)" : "🔄 Atualizar agora"}
                </button>
              )}
              <button onClick={logout} className={menuItemCls}>
                Sair
              </button>
            </nav>
          </aside>
        </div>
      )}

      {carregando ? (
        <div className="animate-pulse text-zinc-500">Carregando dados...</div>
      ) : dados ? (
        <div className="space-y-6">
          <KPICards
            buy={cont.buy}
            hold={cont.hold}
            sell={cont.sell}
            ultima_atualizacao={dados.data}
          />
          <section>
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-zinc-400">
              Top 5 Oportunidades
            </h2>
            <Top5Cards resultados={dados.top5.length ? dados.top5 : dados.resultados} />
          </section>
          <section>
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-zinc-400">
              Scan ({dados.resultados.length} ativos)
            </h2>
            <ScanTable resultados={dados.resultados} />
          </section>
        </div>
      ) : (
        <div className="text-zinc-500">Sem dados disponíveis.</div>
      )}
    </main>
  );
}
