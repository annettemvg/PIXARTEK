"use client";
import { useState } from "react";
import { useProfileStore, AVATARS } from "@/lib/profile-store";

interface Props {
  onDone: () => void;
}

export default function ProfilePicker({ onDone }: Props) {
  const { setProfile } = useProfileStore();
  const [name, setName] = useState("");
  const [avatar, setAvatar] = useState(AVATARS[0]);
  const [error, setError] = useState("");

  function handleConfirm() {
    const trimmed = name.trim();
    if (!trimmed) { setError("Escribe tu nombre para continuar"); return; }
    setProfile({ id: Date.now().toString(), name: trimmed, avatar });
    onDone();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="bg-pixartek-ink border border-white/10 rounded-2xl p-8 w-full max-w-sm flex flex-col gap-6">

        <div className="text-center">
          <p className="text-2xl mb-1">{avatar}</p>
          <h2 className="text-xl font-bold">¿Quién eres?</h2>
          <p className="text-sm text-gray-400 mt-1">Elige tu avatar y escribe tu nombre</p>
        </div>

        {/* Avatar selector */}
        <div className="grid grid-cols-4 gap-2">
          {AVATARS.map(a => (
            <button
              key={a}
              onClick={() => setAvatar(a)}
              className={`text-2xl p-2 rounded-xl transition border ${
                avatar === a
                  ? "border-pixartek-accent bg-pixartek-accent/20"
                  : "border-white/10 hover:bg-white/10"
              }`}
            >
              {a}
            </button>
          ))}
        </div>

        {/* Name input */}
        <div className="flex flex-col gap-1">
          <input
            type="text"
            placeholder="Tu nombre"
            value={name}
            onChange={e => { setName(e.target.value); setError(""); }}
            onKeyDown={e => e.key === "Enter" && handleConfirm()}
            maxLength={30}
            className="w-full bg-white/5 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-pixartek-accent transition"
          />
          {error && <p className="text-xs text-red-400">{error}</p>}
        </div>

        <button
          onClick={handleConfirm}
          className="w-full py-3 rounded-xl bg-pixartek-accent font-semibold hover:opacity-90 transition"
        >
          Comenzar
        </button>
      </div>
    </div>
  );
}
