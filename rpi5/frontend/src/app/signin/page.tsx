"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore, type PixiUser } from "@/lib/auth-store";
import PixartekLogo from "@/components/ui/PixartekLogo";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? "";

const BASE = typeof window !== "undefined"
  ? `http://${window.location.hostname}:8000`
  : "http://localhost:8000";

declare global {
  interface Window {
    google?: {
      accounts: { id: { initialize: (c: object) => void; renderButton: (el: HTMLElement, c: object) => void } };
    };
  }
}

function parseJwt(token: string) {
  return JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
}

type Mode = "choose" | "login" | "register";

export default function SignInPage() {
  const router = useRouter();
  const { user, setUser } = useAuthStore();
  const [hydrated, setHydrated] = useState(false);
  const [mode, setMode] = useState<Mode>("choose");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const googleBtnRef = useRef<HTMLDivElement>(null);

  useEffect(() => { setHydrated(true); }, []);
  useEffect(() => {
    if (hydrated && user) router.replace("/catalog");
  }, [hydrated, user, router]);

  // Google Sign-In
  useEffect(() => {
    if (mode !== "choose" || !GOOGLE_CLIENT_ID) return;
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => {
      window.google?.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: (response: { credential: string }) => {
          const p = parseJwt(response.credential);
          setUser({ id: p.sub, name: p.name, email: p.email, picture: p.picture, level: "principiante" });
          router.push("/catalog");
        },
      });
      if (googleBtnRef.current) {
        window.google?.accounts.id.renderButton(googleBtnRef.current, {
          theme: "outline", size: "large", text: "continue_with", shape: "pill", width: 280,
        });
      }
    };
    document.head.appendChild(script);
    return () => { if (document.head.contains(script)) document.head.removeChild(script); };
  }, [mode, setUser, router]);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      const res = await fetch(`${BASE}/api/users/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) { const d = await res.json(); setError(d.detail ?? "Error al iniciar sesión"); return; }
      const data: PixiUser = await res.json();
      setUser(data);
      router.push("/catalog");
    } catch { setError("No se pudo conectar al servidor."); }
    finally { setLoading(false); }
  }

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      const res = await fetch(`${BASE}/api/users/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password, name: name || username }),
      });
      if (!res.ok) { const d = await res.json(); setError(d.detail ?? "Error al registrarse"); return; }
      const data: PixiUser = await res.json();
      setUser(data);
      router.push("/catalog");
    } catch { setError("No se pudo conectar al servidor."); }
    finally { setLoading(false); }
  }

  return (
    <div className="min-h-screen bg-pixartek-cream flex flex-col items-center justify-center gap-8 px-4">
      <div className="bg-white rounded-3xl shadow-xl border border-pixartek-border p-8 flex flex-col items-center gap-5 w-full max-w-sm">
        <span style={{ fontSize: 44 }}>🎨</span>
        <h1 className="font-display font-700 text-xl text-pixartek-ink">
          {mode === "choose" ? "¡Bienvenido!" : mode === "login" ? "Iniciar sesión" : "Crear cuenta"}
        </h1>

        {/* ── CHOOSE MODE ── */}
        {mode === "choose" && (
          <div className="flex flex-col items-center gap-3 w-full">
            <p className="font-body text-pixartek-muted text-xs text-center leading-relaxed">
              Inicia sesión para que Pixi recuerde tu progreso y personalice tu aprendizaje.
            </p>
            {GOOGLE_CLIENT_ID && <div ref={googleBtnRef} className="mt-1" />}
            <div className="flex items-center gap-3 w-full my-1">
              <div className="flex-1 h-px bg-pixartek-border" />
              <span className="font-body text-xs text-pixartek-muted">o</span>
              <div className="flex-1 h-px bg-pixartek-border" />
            </div>
            <button onClick={() => setMode("login")}
              className="w-full py-3 rounded-full border-2 border-pixartek-coral text-pixartek-coral font-display font-700 text-sm hover:bg-pixartek-coral/5 transition">
              Iniciar con usuario y contraseña
            </button>
            <button onClick={() => setMode("register")}
              className="w-full py-3 rounded-full bg-pixartek-coral text-white font-display font-700 text-sm hover:opacity-90 transition">
              Crear cuenta nueva
            </button>

            {/* ── GUEST OPTION ── */}
            <div className="flex items-center gap-3 w-full mt-1">
              <div className="flex-1 h-px bg-pixartek-border" />
              <span className="font-body text-xs text-pixartek-muted">o</span>
              <div className="flex-1 h-px bg-pixartek-border" />
            </div>
            <button
              onClick={() => {
                setUser({ id: `guest-${Date.now()}`, name: "Invitado", level: "principiante", guest: true });
                router.push("/catalog");
              }}
              className="w-full py-3 rounded-full border-2 border-pixartek-border text-pixartek-muted font-display font-700 text-sm hover:border-pixartek-ink hover:text-pixartek-ink transition">
              Continuar sin cuenta 👤
            </button>
          </div>
        )}

        {/* ── LOGIN FORM ── */}
        {mode === "login" && (
          <form onSubmit={handleLogin} className="flex flex-col gap-3 w-full">
            <input
              value={username} onChange={e => setUsername(e.target.value)}
              placeholder="Nombre de usuario"
              required autoFocus
              className="w-full px-4 py-3 rounded-xl border-2 border-pixartek-border font-body text-sm text-pixartek-ink placeholder:text-pixartek-muted outline-none focus:border-pixartek-coral transition"
            />
            <input
              type="password" value={password} onChange={e => setPassword(e.target.value)}
              placeholder="Contraseña"
              required
              className="w-full px-4 py-3 rounded-xl border-2 border-pixartek-border font-body text-sm text-pixartek-ink placeholder:text-pixartek-muted outline-none focus:border-pixartek-coral transition"
            />
            {error && <p className="font-body text-xs text-red-500 text-center">{error}</p>}
            <button type="submit" disabled={loading}
              className="w-full py-3 rounded-full bg-pixartek-coral text-white font-display font-700 text-sm disabled:opacity-60 hover:opacity-90 transition">
              {loading ? "Entrando..." : "Entrar"}
            </button>
            <button type="button" onClick={() => { setMode("choose"); setError(""); }}
              className="font-body text-xs text-pixartek-muted hover:text-pixartek-coral transition text-center">
              ← Volver
            </button>
          </form>
        )}

        {/* ── REGISTER FORM ── */}
        {mode === "register" && (
          <form onSubmit={handleRegister} className="flex flex-col gap-3 w-full">
            <input
              value={name} onChange={e => setName(e.target.value)}
              placeholder="Tu nombre (ej: María)"
              autoFocus
              className="w-full px-4 py-3 rounded-xl border-2 border-pixartek-border font-body text-sm text-pixartek-ink placeholder:text-pixartek-muted outline-none focus:border-pixartek-coral transition"
            />
            <input
              value={username} onChange={e => setUsername(e.target.value)}
              placeholder="Nombre de usuario"
              required
              className="w-full px-4 py-3 rounded-xl border-2 border-pixartek-border font-body text-sm text-pixartek-ink placeholder:text-pixartek-muted outline-none focus:border-pixartek-coral transition"
            />
            <input
              type="password" value={password} onChange={e => setPassword(e.target.value)}
              placeholder="Contraseña"
              required
              className="w-full px-4 py-3 rounded-xl border-2 border-pixartek-border font-body text-sm text-pixartek-ink placeholder:text-pixartek-muted outline-none focus:border-pixartek-coral transition"
            />
            {error && <p className="font-body text-xs text-red-500 text-center">{error}</p>}
            <button type="submit" disabled={loading}
              className="w-full py-3 rounded-full bg-pixartek-coral text-white font-display font-700 text-sm disabled:opacity-60 hover:opacity-90 transition">
              {loading ? "Creando cuenta..." : "Crear cuenta"}
            </button>
            <button type="button" onClick={() => { setMode("choose"); setError(""); }}
              className="font-body text-xs text-pixartek-muted hover:text-pixartek-coral transition text-center">
              ← Volver
            </button>
          </form>
        )}
      </div>

      <p className="font-body text-xs text-pixartek-muted/50 text-center max-w-xs">
        Tu información solo se usa para personalizar tu experiencia con Pixi.
      </p>
    </div>
  );
}
