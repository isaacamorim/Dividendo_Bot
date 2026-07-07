"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { HistoricoResponse } from "@/types";
import ScoreChart from "@/components/ScoreChart";
import PriceChart from "@/components/PriceChart";

const API = process.env.NEXT_PUBLIC_API_URL || "";
const WATCHLIST = [
  // Bancos
  "BBAS3",
  "ITUB4",
  "BBDC4",

  // Energia
  "TAEE11",
  "ISAE4",
  "CMIG4",
  "CPLE3",
  "EGIE3",

  // Commodities
  "PETR4",
  "VALE3",

  // Telecom
  "VIVT3",

  // Industrial
  "WEGE3",

  // Tecnologia
  "TOTS3",

  // Saúde
  "RADL3",
  "RDOR3",

  // Consumo
  "ABEV3",
  "LREN3",

  // Seguros
  "CXSE3",

  // Papel e Celulose
  "SUZB3",

  // Shopping
  "MULT3",
];

const num = (v: number | null, d = 2) => (v == null ? "—" : v.toFixed(d));
const ddmm = (s: string) => {
  const p = s.split("-");
  return `${p[2]}/${p[1]}`;
};
const sinalCor = (s: string) =>
  s === "BUY" ? "text-emerald-400" : s === "SELL" ? "text-red-400" : "text-amber-400";

export default function Historico() {
  const router = useRouter();
  const [ticker, setTicker] = useState("PETR4");
  const [dados, setDados] = useState<HistoricoResponse | null>(null);
  const [carregando, setCarregando] = useState(true);

  const carregar = useCallback(
    async (tk: string) => {
      setCarregando(true);
      try {
        const resp = await fetch(`${API}/scan/historico/${tk}?dias=30`, {
          credentials: "include",
        });
        if (resp.status === 401) {
          router.push("/login");
          return;
        }
        setDados(await resp.json());
      } catch {
        // silencioso
      } finally {
        setCarregando(false);
      }
    },
    [router],
  );

  useEffect(() => {
    carregar(ticker);
  }, [ticker, carregar]);

  return (
    <main className="mx-auto max-w-6xl px-4 py-6">
      <header className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-bold">📈 Histórico de Score</h1>
        <Link
          href="/dashboard"
          className="rounded-lg bg-zinc-800 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-700"
        >
          ← Dashboard
        </Link>
      </header>

      <div className="mb-6">
        <label className="mb-1 block text-sm text-zinc-400">Ativo</label>
        <select
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 outline-none focus:border-emerald-500"
        >
          {WATCHLIST.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      {carregando ? (
        <div className="animate-pulse text-zinc-500">Carregando...</div>
      ) : dados ? (
        <div className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            <ScoreChart serie={dados.serie} />
            <PriceChart serie={dados.serie} />
          </div>

          <div className="overflow-x-auto rounded-xl border border-zinc-800">
            <table className="w-full text-sm">
              <thead className="bg-zinc-900 text-zinc-400">
                <tr>
                  {[
                    "Data",
                    "Score",
                    "Sinal",
                    "Preço",
                    "P.Justo",
                    "Upside",
                    "DY",
                    "ROE",
                    "Dív/EBITDA",
                    "Payout",
                    "Cresc.LPA",
                  ].map((h) => (
                      <th key={h} className="px-3 py-2 text-left">
                        {h}
                      </th>
                    ),
                  )}
                </tr>
              </thead>
              <tbody>
                {[...dados.serie].reverse().map((p) => (
                  <tr key={p.data} className="border-t border-zinc-800">
                    <td className="px-3 py-2">{ddmm(p.data)}</td>
                    <td className="px-3 py-2 font-semibold">{num(p.score, 1)}</td>
                    <td className={`px-3 py-2 font-semibold ${sinalCor(p.sinal)}`}>{p.sinal}</td>
                    <td className="px-3 py-2">R${num(p.preco)}</td>
                    <td className="px-3 py-2">R${num(p.preco_justo)}</td>
                    <td
                      className={`px-3 py-2 ${
                        (p.upside ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"
                      }`}
                    >
                      {p.upside == null
                        ? "—"
                        : `${p.upside > 0 ? "+" : ""}${p.upside.toFixed(0)}%`}
                    </td>
                    <td className="px-3 py-2">{num(p.dy, 1)}%</td>
                    <td className="px-3 py-2">{num(p.roe, 1)}%</td>
                    <td className="px-3 py-2">
                      {p.divida_ebitda == null ? "—" : `${p.divida_ebitda.toFixed(1)}x`}
                    </td>
                    <td className="px-3 py-2">{num(p.payout, 0)}%</td>
                    <td
                      className={`px-3 py-2 ${
                        p.eps_growth == null
                          ? ""
                          : p.eps_growth >= 0
                            ? "text-emerald-400"
                            : "text-red-400"
                      }`}
                    >
                      {p.eps_growth == null
                        ? "—"
                        : `${p.eps_growth > 0 ? "+" : ""}${p.eps_growth.toFixed(0)}%`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="text-zinc-500">Sem dados.</div>
      )}
    </main>
  );
}
