"use client";

import { useCallback, useEffect, useState } from "react";
import { Alerta, AlertasResponse } from "@/types";

const API = process.env.NEXT_PUBLIC_API_URL || "";
const POLL_MS = 5 * 60 * 1000; // 5 minutos

const corTipo = (tipo: string) => {
  if (tipo === "NOVO_BUY" || tipo === "TAKE_PROFIT") return "text-emerald-400";
  if (tipo === "SAIU_BUY") return "text-amber-400";
  if (tipo === "STOP_LOSS") return "text-red-400";
  return "text-zinc-300";
};

const rotuloTipo = (tipo: string) =>
  ({
    NOVO_BUY: "NOVO BUY",
    SAIU_BUY: "SAIU DO BUY",
    STOP_LOSS: "STOP LOSS",
    TAKE_PROFIT: "TAKE PROFIT",
  })[tipo] ?? tipo;

const horario = (iso: string) => {
  const d = new Date(iso);
  return d.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export default function AlertaBadge() {
  const [alertas, setAlertas] = useState<Alerta[]>([]);
  const [naoLidos, setNaoLidos] = useState(0);
  const [aberto, setAberto] = useState(false);

  const carregar = useCallback(async () => {
    try {
      const resp = await fetch(`${API}/alertas`, { credentials: "include" });
      if (!resp.ok) return;
      const data: AlertasResponse = await resp.json();
      setAlertas(data.alertas);
      setNaoLidos(data.total_nao_lidos);
    } catch {
      // silencioso — mantém estado anterior
    }
  }, []);

  useEffect(() => {
    carregar();
    const id = setInterval(carregar, POLL_MS);
    return () => clearInterval(id);
  }, [carregar]);

  // Título da aba reflete os não lidos.
  useEffect(() => {
    document.title = naoLidos > 0 ? `(${naoLidos}) Dividend Bot` : "Dividend Bot";
  }, [naoLidos]);

  async function marcarTodos() {
    try {
      await fetch(`${API}/alertas/marcar-todos-lidos`, {
        method: "POST",
        credentials: "include",
      });
      await carregar();
    } catch {
      // silencioso
    }
  }

  async function marcarUm(id: number) {
    try {
      await fetch(`${API}/alertas/${id}/lido`, { method: "POST", credentials: "include" });
      await carregar();
    } catch {
      // silencioso
    }
  }

  return (
    <>
      <button
        onClick={() => setAberto(true)}
        className="relative rounded-lg bg-zinc-800 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-700"
        aria-label="Alertas"
      >
        🔔
        {naoLidos > 0 && (
          <span className="absolute -right-1 -top-1 flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-red-600 px-1 text-xs font-bold text-white">
            {naoLidos > 99 ? "99+" : naoLidos}
          </span>
        )}
      </button>

      {aberto && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setAberto(false)}
            aria-hidden
          />
          <aside className="relative flex h-full w-full max-w-md flex-col border-l border-zinc-800 bg-zinc-950 shadow-xl">
            <header className="flex items-center justify-between border-b border-zinc-800 px-4 py-3">
              <h2 className="text-sm font-semibold text-zinc-200">
                🔔 Alertas {naoLidos > 0 && <span className="text-red-400">({naoLidos})</span>}
              </h2>
              <div className="flex gap-2">
                {naoLidos > 0 && (
                  <button
                    onClick={marcarTodos}
                    className="rounded-lg bg-zinc-800 px-2 py-1 text-xs text-zinc-300 hover:bg-zinc-700"
                  >
                    Marcar todos como lidos
                  </button>
                )}
                <button
                  onClick={() => setAberto(false)}
                  className="rounded-lg bg-zinc-800 px-2 py-1 text-xs text-zinc-300 hover:bg-zinc-700"
                >
                  Fechar
                </button>
              </div>
            </header>

            <div className="flex-1 overflow-y-auto">
              {alertas.length === 0 ? (
                <p className="px-4 py-8 text-center text-sm text-zinc-500">Nenhum alerta ainda.</p>
              ) : (
                <ul className="divide-y divide-zinc-900">
                  {alertas.map((a) => (
                    <li
                      key={a.id}
                      onClick={() => !a.lido && marcarUm(a.id)}
                      className={`cursor-pointer px-4 py-3 hover:bg-zinc-900 ${
                        a.lido ? "opacity-50" : ""
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className={`text-xs font-bold ${corTipo(a.tipo)}`}>
                          {rotuloTipo(a.tipo)} · {a.ticker}
                        </span>
                        <span className="text-xs text-zinc-500">{horario(a.created_at)}</span>
                      </div>
                      <p className="mt-1 text-sm text-zinc-300">{a.mensagem}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </aside>
        </div>
      )}
    </>
  );
}
