import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Protege /dashboard (precisa do cookie httpOnly "token"); manda quem já
// está logado direto pro dashboard se tentar abrir /login.
export function middleware(request: NextRequest) {
  const token = request.cookies.get("token")?.value;
  const { pathname } = request.nextUrl;

  if (pathname.startsWith("/dashboard") && !token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  if (pathname === "/login" && token) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/login"],
};
