"use client";

import { useRouter } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_URL || "";

// O token é cookie httpOnly — o JS NÃO consegue lê-lo (por design). A proteção
// de rotas é feita pelo middleware (server-side). Aqui só expomos o logout.
export function useAuth() {
  const router = useRouter();

  async function logout() {
    try {
      await fetch(`${API}/auth/logout`, { method: "POST", credentials: "include" });
    } catch {
      // ignora — o cookie expira sozinho; seguimos pro login
    }
    router.push("/login");
    router.refresh();
  }

  return { logout };
}
