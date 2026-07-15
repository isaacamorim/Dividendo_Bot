"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_URL || "";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);

  async function entrar() {
    setErro("");
    setCarregando(true);
    try {
      const resp = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include", // recebe o cookie httpOnly
        body: JSON.stringify({ username, password }),
      });

      if (resp.status === 401) {
        setErro("Usuário ou senha incorretos");
        return;
      }
      if (!resp.ok) {
        setErro("Serviço indisponível");
        return;
      }
      router.push("/dashboard");
      router.refresh();
    } catch {
      setErro("Serviço indisponível");
    } finally {
      setCarregando(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-950 px-4 text-zinc-100">
      <div className="w-full max-w-sm rounded-2xl border border-zinc-800 bg-zinc-900 p-8 shadow-xl">
        <h1 className="mb-1 text-center text-2xl font-bold">📊 Dividend Bot B3</h1>
        <p className="mb-6 text-center text-sm text-zinc-400">Acesso ao painel</p>

        <label className="mb-1 block text-sm text-zinc-400">Usuário</label>
        <input
          className="mb-4 w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-3 outline-none focus:border-emerald-500"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && entrar()}
          autoFocus
        />

        <label className="mb-1 block text-sm text-zinc-400">Senha</label>
        <input
          type="password"
          className="mb-4 w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-3 outline-none focus:border-emerald-500"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && entrar()}
        />

        {erro && (
          <p className="mb-4 rounded-lg bg-red-950 px-3 py-2 text-sm text-red-400">
            {erro}
          </p>
        )}

        <button
          onClick={entrar}
          disabled={carregando || !username || !password}
          className="min-h-[48px] w-full rounded-lg bg-emerald-600 px-3 py-3 font-medium text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {carregando ? "Entrando..." : "Entrar"}
        </button>
      </div>
    </main>
  );
}
