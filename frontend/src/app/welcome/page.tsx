"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useProfileStore } from "@/lib/profile-store";
import PixartekLogo from "@/components/ui/PixartekLogo";

export default function WelcomePage() {
  const router = useRouter();
  const { profile } = useProfileStore();
  const [progress, setProgress] = useState(0);
  const [ready, setReady] = useState(false);

  // If no profile, send back to home
  useEffect(() => {
    if (!profile) { router.replace("/"); return; }
    setReady(true);

    // Animate progress bar over 3 seconds then redirect
    const start = Date.now();
    const duration = 3000;
    const interval = setInterval(() => {
      const elapsed = Date.now() - start;
      const pct = Math.min((elapsed / duration) * 100, 100);
      setProgress(pct);
      if (pct >= 100) {
        clearInterval(interval);
        router.push("/catalog");
      }
    }, 30);

    return () => clearInterval(interval);
  }, [profile, router]);

  if (!ready || !profile) return null;

  // Color sequence for animated dots
  const colors = ["#E07B6A", "#D4B85A", "#7DC4A8", "#7096BC", "#A495C0", "#D498B8"];

  return (
    <main className="flex flex-col items-center justify-center min-h-screen bg-pixartek-cream px-6 relative overflow-hidden">

      {/* Background blobs */}
      <div className="absolute top-0 left-0 w-80 h-80 rounded-full bg-pixartek-mint/25 blur-3xl pointer-events-none -translate-x-1/2 -translate-y-1/2" />
      <div className="absolute bottom-0 right-0 w-96 h-96 rounded-full bg-pixartek-blush/20 blur-3xl pointer-events-none translate-x-1/3 translate-y-1/3" />
      <div className="absolute top-1/2 left-1/2 w-64 h-64 rounded-full bg-pixartek-yellow/15 blur-3xl pointer-events-none -translate-x-1/2 -translate-y-1/2" />

      <div className="relative z-10 flex flex-col items-center gap-8 text-center max-w-lg">

        {/* Logo */}
        <div className="animate-fade-in">
          <PixartekLogo size="md" />
        </div>

        {/* Avatar */}
        <div
          className="text-8xl animate-scale-in opacity-0-init"
          style={{ animationDelay: "200ms", animationFillMode: "forwards" }}
        >
          {profile.avatar}
        </div>

        {/* Greeting */}
        <div
          className="animate-fade-up opacity-0-init"
          style={{ animationDelay: "350ms", animationFillMode: "forwards" }}
        >
          <h1 className="font-display font-800 text-5xl text-pixartek-ink leading-tight">
            ¡Bienvenido/a,
          </h1>
          <h2 className="font-display font-800 text-5xl text-pixartek-coral mt-1">
            {profile.name}!
          </h2>
        </div>

        {/* Subtitle */}
        <p
          className="font-body text-pixartek-muted text-xl leading-relaxed animate-fade-up opacity-0-init"
          style={{ animationDelay: "500ms", animationFillMode: "forwards" }}
        >
          Estás listo para comenzar tu<br />
          <span className="text-pixartek-ink font-semibold">experiencia artística</span>
        </p>

        {/* Animated color dots */}
        <div
          className="flex gap-3 animate-fade-in opacity-0-init"
          style={{ animationDelay: "650ms", animationFillMode: "forwards" }}
        >
          {colors.map((c, i) => (
            <div
              key={i}
              className="w-3 h-3 rounded-full dot-bounce"
              style={{
                backgroundColor: c,
                animationDelay: `${i * 0.15}s`,
              }}
            />
          ))}
        </div>

        {/* Progress + CTA */}
        <div
          className="w-full max-w-sm animate-fade-up opacity-0-init"
          style={{ animationDelay: "700ms", animationFillMode: "forwards" }}
        >
          {/* Auto-progress bar */}
          <div className="h-1.5 bg-pixartek-border rounded-full overflow-hidden mb-5">
            <div
              className="h-full rounded-full transition-none"
              style={{
                width: `${progress}%`,
                background: "linear-gradient(90deg, #E07B6A, #D4B85A, #7DC4A8, #7096BC)",
              }}
            />
          </div>

          <button
            onClick={() => router.push("/catalog")}
            className="
              w-full py-5 rounded-2xl font-display font-800 text-xl text-white
              bg-pixartek-coral shadow-btn
              hover:opacity-90 active:scale-[0.98] transition-all duration-150
            "
          >
            Ver catálogo de obras →
          </button>
        </div>
      </div>
    </main>
  );
}
