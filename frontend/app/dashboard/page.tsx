"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ScanLatest } from "@/types";
import { useAuth } from "@/hooks/useAuth";
import KPICards from "@/components/KPICards";
import Top5Cards from "@/components/Top5Cards";
import ScanTable from "@/components/ScanTable";

const API = process.env.NEXT_PUBLIC_API_URL || "";

export default function Dashboard() {
  const router = useRouter();
  const { logout } = useAuth();
  const [dados, setDados] = useState<ScanLatest | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [escaneando, setEscaneando] = useState(false);

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
      <header className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-bold">📊 Dividend Bot B3</h1>
        <div className="flex gap-2">
          <button
            onClick={atualizar}
            disabled={escaneando}
            className="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {escaneando ? "Escaneando... (~30s)" : "🔄 Atualizar agora"}
          </button>
          <button
            onClick={logout}
            className="rounded-lg bg-zinc-800 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-700"
          >
            Sair
          </button>
        </div>
      </header>

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
