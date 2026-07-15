"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { CarteiraResumo } from "@/types";
import CarteiraPie from "@/components/CarteiraPie";

const API = process.env.NEXT_PUBLIC_API_URL || "";
const brl = (v: number) => `R$${v.toFixed(2)}`;
const hoje = () => new Date().toISOString().slice(0, 10);
const corVal = (v: number) => (v >= 0 ? "text-emerald-400" : "text-red-400");

const inputCls =
  "w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm outline-none focus:border-emerald-500";

export default function Carteira() {
  const router = useRouter();
  const [dados, setDados] = useState<CarteiraResumo | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [msg, setMsg] = useState("");

  // formulário posição
  const [pTicker, setPTicker] = useState("");
  const [pPreco, setPPreco] = useState("");
  const [pQtd, setPQtd] = useState("");
  const [pData, setPData] = useState(hoje());
  const [pNota, setPNota] = useState("");

  // formulário dividendo
  const [dTicker, setDTicker] = useState("");
  const [dValor, setDValor] = useState("");
  const [dData, setDData] = useState(hoje());

  const carregar = useCallback(async () => {
    try {
      const resp = await fetch(`${API}/carteira`, { credentials: "include" });
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
  }, [router]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  async function addPosicao() {
    setMsg("");
    const resp = await fetch(`${API}/carteira/posicao`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ticker: pTicker,
        preco_compra: parseFloat(pPreco),
        quantidade: parseInt(pQtd, 10),
        data_compra: pData,
        nota: pNota || null,
      }),
    });
    if (resp.ok) {
      setPTicker("");
      setPPreco("");
      setPQtd("");
      setPNota("");
      await carregar();
      setMsg("Posição adicionada.");
    } else {
      setMsg("Erro ao adicionar posição.");
    }
  }

  async function addDividendo() {
    setMsg("");
    const resp = await fetch(`${API}/carteira/dividendo`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ticker: dTicker,
        valor_por_acao: parseFloat(dValor),
        data_pagamento: dData,
      }),
    });
    if (resp.ok) {
      setDTicker("");
      setDValor("");
      await carregar();
      setMsg("Dividendo registrado.");
    } else {
      setMsg("Erro ao registrar dividendo.");
    }
  }

  const cards = dados
    ? [
        { label: "Total investido", value: brl(dados.total_investido), cor: "text-zinc-100" },
        { label: "Valor atual", value: brl(dados.total_atual), cor: "text-zinc-100" },
        { label: "Lucro de capital", value: brl(dados.lucro_capital), cor: corVal(dados.lucro_capital) },
        { label: "Dividendos", value: brl(dados.total_dividendos), cor: "text-emerald-400" },
        {
          label: "Retorno total",
          value: `${dados.rent_total_pct >= 0 ? "+" : ""}${dados.rent_total_pct}%`,
          cor: corVal(dados.rent_total_pct),
        },
      ]
    : [];

  return (
    <main className="mx-auto max-w-6xl px-4 py-6">
      <header className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-bold">💼 Minha Carteira</h1>
        <Link
          href="/dashboard"
          className="rounded-lg bg-zinc-800 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-700"
        >
          ← Dashboard
        </Link>
      </header>

      {carregando ? (
        <div className="animate-pulse text-zinc-500">Carregando carteira...</div>
      ) : dados ? (
        <div className="space-y-6">
          {/* Cards de resumo */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {cards.map((c) => (
              <div key={c.label} className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
                <div className="text-xs uppercase tracking-wide text-zinc-500">{c.label}</div>
                <div className={`mt-1 text-lg font-bold ${c.cor}`}>{c.value}</div>
              </div>
            ))}
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            {/* Posições */}
            <div className="lg:col-span-2">
            {/* Tabela — sm+ */}
            <div className="hidden overflow-x-auto rounded-xl border border-zinc-800 sm:block">
              <table className="w-full text-sm">
                <thead className="bg-zinc-900 text-zinc-400">
                  <tr>
                    {["Ticker", "Qtd", "PM", "Atual", "Investido", "V.Atual", "Rent.%", "Div", "Ret.Tot%"].map(
                      (h) => (
                        <th key={h} className="px-3 py-2 text-left">
                          {h}
                        </th>
                      ),
                    )}
                  </tr>
                </thead>
                <tbody>
                  {dados.posicoes.map((p) => (
                    <tr
                      key={p.ticker}
                      className={`border-t border-zinc-800 ${
                        p.rentabilidade_pct >= 0 ? "bg-emerald-950/20" : "bg-red-950/20"
                      }`}
                    >
                      <td className="px-3 py-2 font-medium">{p.ticker}</td>
                      <td className="px-3 py-2">{p.qtd}</td>
                      <td className="px-3 py-2">{brl(p.pm)}</td>
                      <td className="px-3 py-2">{brl(p.preco_atual)}</td>
                      <td className="px-3 py-2">{brl(p.investido)}</td>
                      <td className="px-3 py-2">{brl(p.atual)}</td>
                      <td className={`px-3 py-2 font-semibold ${corVal(p.rentabilidade_pct)}`}>
                        {p.rentabilidade_pct >= 0 ? "+" : ""}
                        {p.rentabilidade_pct}%
                      </td>
                      <td className="px-3 py-2">{brl(p.dividendos)}</td>
                      <td className={`px-3 py-2 font-semibold ${corVal(p.rent_total_pct)}`}>
                        {p.rent_total_pct >= 0 ? "+" : ""}
                        {p.rent_total_pct}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Cards — mobile (<sm) */}
            <div className="space-y-3 sm:hidden">
              {dados.posicoes.map((p) => (
                <div
                  key={p.ticker}
                  className={`rounded-xl border border-zinc-800 p-4 ${
                    p.rentabilidade_pct >= 0 ? "bg-emerald-950/20" : "bg-red-950/20"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-bold">{p.ticker}</span>
                    <span className={`text-sm font-semibold ${corVal(p.rent_total_pct)}`}>
                      Ret. {p.rent_total_pct >= 0 ? "+" : ""}
                      {p.rent_total_pct}%
                    </span>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-zinc-300">
                    <span>Qtd: {p.qtd}</span>
                    <span>PM: {brl(p.pm)}</span>
                    <span>Atual: {brl(p.preco_atual)}</span>
                  </div>
                  <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-zinc-300">
                    <span>Investido: {brl(p.investido)}</span>
                    <span>V.Atual: {brl(p.atual)}</span>
                  </div>
                  <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-zinc-300">
                    <span>
                      Rent.:{" "}
                      <span className={`font-semibold ${corVal(p.rentabilidade_pct)}`}>
                        {p.rentabilidade_pct >= 0 ? "+" : ""}
                        {p.rentabilidade_pct}%
                      </span>
                    </span>
                    <span>Div: {brl(p.dividendos)}</span>
                  </div>
                </div>
              ))}
            </div>
            </div>

            {/* Pizza */}
            <CarteiraPie posicoes={dados.posicoes} />
          </div>

          {msg && (
            <p className="rounded-lg bg-zinc-800 px-3 py-2 text-sm text-emerald-400">{msg}</p>
          )}

          {/* Formulários */}
          <div className="grid gap-6 md:grid-cols-2">
            <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
              <h3 className="mb-3 text-sm font-semibold text-zinc-400">Adicionar posição</h3>
              <div className="grid grid-cols-2 gap-2">
                <input className={inputCls} placeholder="Ticker" value={pTicker} onChange={(e) => setPTicker(e.target.value)} />
                <input className={inputCls} placeholder="Preço" type="number" value={pPreco} onChange={(e) => setPPreco(e.target.value)} />
                <input className={inputCls} placeholder="Quantidade" type="number" value={pQtd} onChange={(e) => setPQtd(e.target.value)} />
                <input className={inputCls} type="date" value={pData} onChange={(e) => setPData(e.target.value)} />
                <input className={`${inputCls} col-span-2`} placeholder="Nota (opcional)" value={pNota} onChange={(e) => setPNota(e.target.value)} />
              </div>
              <button
                onClick={addPosicao}
                disabled={!pTicker || !pPreco || !pQtd}
                className="mt-3 w-full rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
              >
                Adicionar
              </button>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
              <h3 className="mb-3 text-sm font-semibold text-zinc-400">Registrar dividendo</h3>
              <div className="grid grid-cols-2 gap-2">
                <input className={inputCls} placeholder="Ticker" value={dTicker} onChange={(e) => setDTicker(e.target.value)} />
                <input className={inputCls} placeholder="Valor/ação" type="number" value={dValor} onChange={(e) => setDValor(e.target.value)} />
                <input className={`${inputCls} col-span-2`} type="date" value={dData} onChange={(e) => setDData(e.target.value)} />
              </div>
              <button
                onClick={addDividendo}
                disabled={!dTicker || !dValor}
                className="mt-3 w-full rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
              >
                Registrar
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-zinc-500">Sem dados.</div>
      )}
    </main>
  );
}
