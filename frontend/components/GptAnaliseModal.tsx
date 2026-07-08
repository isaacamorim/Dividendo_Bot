"use client";

import { useEffect, useState } from "react";
import { GptResponse } from "@/types";

const API = process.env.NEXT_PUBLIC_API_URL || "";

const bolinhas = (c: string) => (c === "alta" ? "●●●" : c === "media" ? "●●○" : "●○○");
const rotuloConf = (c: string) => (c === "alta" ? "Alta" : c === "media" ? "Média" : "Baixa");

export default function GptAnaliseModal({
  ticker,
  onClose,
}: {
  ticker: string;
  onClose: () => void;
}) {
  const [data, setData] = useState<GptResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState(false);

  useEffect(() => {
    let vivo = true;
    (async () => {
      try {
        const resp = await fetch(`${API}/scan/analisar-gpt/${ticker}`, {
          credentials: "include",
        });
        const d: GptResponse = await resp.json();
        if (!vivo) return;
        if (!resp.ok || !d.disponivel || !d.analise) setErro(true);
        else setData(d);
      } catch {
        if (vivo) setErro(true);
      } finally {
        if (vivo) setLoading(false);
      }
    })();
    return () => {
      vivo = false;
    };
  }, [ticker]);

  const a = data?.analise;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} aria-hidden />
      <div className="relative w-full max-w-lg rounded-xl border border-zinc-800 bg-zinc-950 p-5 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-zinc-100">🤖 Análise GPT — {ticker}</h2>
          <button
            onClick={onClose}
            className="rounded-lg bg-zinc-800 px-2 py-1 text-xs text-zinc-300 hover:bg-zinc-700"
          >
            Fechar
          </button>
        </div>

        {loading ? (
          <div className="flex items-center gap-3 py-10 text-sm text-zinc-400">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-zinc-600 border-t-emerald-400" />
            Analisando com IA...
          </div>
        ) : erro || !a ? (
          <p className="py-10 text-center text-sm text-zinc-400">
            Análise indisponível no momento.
          </p>
        ) : (
          <div className="space-y-4 text-sm">
            <section>
              <h3 className="mb-1 font-semibold text-zinc-300">📋 Resumo</h3>
              <p className="text-zinc-300">{a.resumo}</p>
            </section>

            {a.pontos_fortes.length > 0 && (
              <section>
                <h3 className="mb-1 font-semibold text-emerald-400">✅ Pontos fortes</h3>
                <ul className="list-disc space-y-1 pl-5 text-zinc-300">
                  {a.pontos_fortes.map((p, i) => (
                    <li key={i}>{p}</li>
                  ))}
                </ul>
              </section>
            )}

            {a.riscos.length > 0 && (
              <section>
                <h3 className="mb-1 font-semibold text-amber-400">⚠️ Riscos</h3>
                <ul className="list-disc space-y-1 pl-5 text-zinc-300">
                  {a.riscos.map((p, i) => (
                    <li key={i}>{p}</li>
                  ))}
                </ul>
              </section>
            )}

            <section>
              <h3 className="mb-1 font-semibold text-zinc-300">💡 Recomendação</h3>
              <p className="text-zinc-300">{a.recomendacao}</p>
            </section>

            <div className="flex items-center justify-between border-t border-zinc-800 pt-3 text-xs text-zinc-500">
              <span>
                Confiança:{" "}
                <span className="text-zinc-300">
                  {bolinhas(a.confianca)} {rotuloConf(a.confianca)}
                </span>
              </span>
              <span>Gerado por GPT-4o-mini</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
