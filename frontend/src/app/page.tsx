"use client";
import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import PixartekLogo from "@/components/ui/PixartekLogo";
import VirtualKeyboard from "@/components/ui/VirtualKeyboard";
import { useProfileStore, AVATARS } from "@/lib/profile-store";

export default function Home() {
  const router = useRouter();
  const { setProfile } = useProfileStore();
  const [name, setName] = useState("");
  const [avatar, setAvatar] = useState(AVATARS[0]);
  const [step, setStep] = useState<"name" | "avatar">("name");
  const [shake, setShake] = useState(false);
  const [kbVisible, setKbVisible] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleNameNext() {
    if (!name.trim()) {
      setShake(true);
      setTimeout(() => setShake(false), 500);
      inputRef.current?.focus();
      return;
    }
    setStep("avatar");
  }

  function handleStart() {
    setProfile({ id: `user-${Date.now()}`, name: name.trim(), avatar });
    router.push("/welcome");
  }

  return (
    <main className="flex flex-col items-center justify-center min-h-screen bg-pixartek-cream px-6 relative overflow-hidden">

      {/* Decorative paint blobs */}
      <div className="absolute top-[-60px] left-[-60px] w-64 h-64 rounded-full bg-pixartek-mint/20 blur-3xl pointer-events-none" />
      <div className="absolute bottom-[-80px] right-[-40px] w-72 h-72 rounded-full bg-pixartek-blush/20 blur-3xl pointer-events-none" />
      <div className="absolute top-1/3 right-[-50px] w-48 h-48 rounded-full bg-pixartek-yellow/15 blur-3xl pointer-events-none" />

      {/* Card */}
      <div className="relative z-10 flex flex-col items-center w-full max-w-md animate-scale-in">

        {/* Logo */}
        <div className="mb-8 animate-fade-up">
          <PixartekLogo size="lg" />
        </div>

        {/* Tagline */}
        <p
          className="font-display text-pixartek-muted text-lg mb-10 text-center animate-fade-up opacity-0-init"
          style={{ animationDelay: "120ms", animationFillMode: "forwards" }}
        >
          Tu estudio de arte personal
        </p>

        {/* Step: Name */}
        {step === "name" && (
          <div
            className="w-full flex flex-col gap-5 animate-fade-up opacity-0-init"
            style={{ animationDelay: "200ms", animationFillMode: "forwards" }}
          >
            <label className="font-display text-2xl font-700 text-pixartek-ink text-center">
              ¿Cuál es tu nombre?
            </label>

            <input
              ref={inputRef}
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              onFocus={() => setKbVisible(true)}
              onKeyDown={e => e.key === "Enter" && handleNameNext()}
              placeholder="Toca aquí para escribir..."
              readOnly
              maxLength={24}
              className={`
                input-painted w-full px-6 py-5 text-xl font-body font-semibold
                text-pixartek-ink placeholder:text-pixartek-border text-center
                transition-all duration-200 cursor-pointer
                ${shake ? "animate-[shake_0.3s_ease]" : ""}
              `}
            />

            <button
              onClick={handleNameNext}
              className="
                w-full py-5 rounded-2xl font-display font-800 text-xl text-white
                bg-pixartek-coral shadow-btn
                hover:opacity-90 active:scale-[0.98] transition-all duration-150
              "
            >
              Continuar →
            </button>
          </div>
        )}

        {/* Step: Avatar */}
        {step === "avatar" && (
          <div className="w-full flex flex-col gap-6 animate-scale-in">
            <div className="text-center">
              <p className="font-display text-2xl font-700 text-pixartek-ink">
                Hola, <span className="text-pixartek-coral">{name}</span> 👋
              </p>
              <p className="text-pixartek-muted mt-1 font-body">Elige tu avatar de artista</p>
            </div>

            <div className="grid grid-cols-4 gap-3">
              {AVATARS.map(av => (
                <button
                  key={av}
                  onClick={() => setAvatar(av)}
                  className={`
                    flex items-center justify-center text-4xl h-18 w-full aspect-square rounded-2xl
                    border-2 transition-all duration-150
                    ${avatar === av
                      ? "border-pixartek-coral bg-pixartek-coral/10 scale-105 shadow-btn"
                      : "border-pixartek-border bg-white hover:border-pixartek-coral/40 hover:scale-105"
                    }
                  `}
                  style={{ fontSize: "2rem", padding: "0.75rem" }}
                >
                  {av}
                </button>
              ))}
            </div>

            <button
              onClick={handleStart}
              className="
                w-full py-5 rounded-2xl font-display font-800 text-xl text-white
                bg-pixartek-coral shadow-btn
                hover:opacity-90 active:scale-[0.98] transition-all duration-150
              "
            >
              {avatar} ¡Empezar!
            </button>

            <button
              onClick={() => setStep("name")}
              className="text-pixartek-muted text-sm font-body hover:text-pixartek-ink transition text-center"
            >
              ← Cambiar nombre
            </button>
          </div>
        )}

        {/* Settings link */}
        <button
          onClick={() => router.push("/settings")}
          className="absolute bottom-[-72px] text-xs text-pixartek-muted/60 hover:text-pixartek-muted transition font-body"
        >
          ⚙ Configuración del sistema
        </button>
      </div>

      {/* Virtual keyboard — shows when name input is focused */}
      <VirtualKeyboard
        visible={kbVisible}
        value={name}
        onChange={setName}
        onDone={() => { setKbVisible(false); handleNameNext(); }}
      />
    </main>
  );
}
