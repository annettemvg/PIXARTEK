"use client";
import { useEffect, useState, useCallback } from "react";

interface Props {
  value: string;
  onChange: (val: string) => void;
  onDone?: () => void;
  visible: boolean;
}

const ROWS = [
  ["q","w","e","r","t","y","u","i","o","p"],
  ["a","s","d","f","g","h","j","k","l"],
  ["⇧","z","x","c","v","b","n","m","⌫"],
  ["123","@","_",    " ",    ".","✓"],
];

const NUM_ROWS = [
  ["1","2","3","4","5","6","7","8","9","0"],
  ["-","_","@",".","!","#","$","%","&","*"],
  ["(",")","+","=","/","\\","'","\"","?","⌫"],
  ["ABC","  ","    " ,"   ","✓"],
];

export default function VirtualKeyboard({ value, onChange, onDone, visible }: Props) {
  const [caps, setCaps] = useState(false);
  const [numMode, setNumMode] = useState(false);

  const handleKey = useCallback((key: string) => {
    if (key === "⌫") {
      onChange(value.slice(0, -1));
    } else if (key === "✓") {
      onDone?.();
    } else if (key === "⇧") {
      setCaps(c => !c);
    } else if (key === "123") {
      setNumMode(true);
    } else if (key === "ABC") {
      setNumMode(false);
    } else {
      const ch = caps && !numMode ? key.toUpperCase() : key;
      onChange(value + ch);
    }
  }, [value, onChange, onDone, caps, numMode]);

  if (!visible) return null;

  const rows = numMode ? NUM_ROWS : ROWS;

  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t-2 border-pixartek-border shadow-2xl"
      style={{ touchAction: "none" }}
    >
      <div className="px-2 py-2 flex flex-col gap-1.5 max-w-2xl mx-auto">
        {rows.map((row, ri) => (
          <div key={ri} className="flex gap-1 justify-center">
            {row.map((key, ki) => {
              const isSpace = key.trim() === "" || key === " ";
              const isSpecial = ["⌫","✓","⇧","123","ABC"].includes(key.trim());
              const isDone = key === "✓";
              return (
                <button
                  key={ki}
                  onPointerDown={(e) => { e.preventDefault(); handleKey(key.trim() || " "); }}
                  className={[
                    "rounded-xl font-display font-700 text-base h-12 transition-all active:scale-95 select-none",
                    isSpace ? "flex-1" :
                    isDone  ? "px-6 bg-pixartek-coral text-white shadow-btn" :
                    isSpecial ? "px-4 bg-pixartek-cream border border-pixartek-border text-pixartek-muted" :
                    "w-9 bg-pixartek-cream border border-pixartek-border text-pixartek-ink hover:bg-white hover:border-pixartek-coral/40",
                    caps && !numMode && !isSpecial && !isDone ? "text-pixartek-coral" : "",
                  ].join(" ")}
                >
                  {key === " " || key.trim() === "" ? "espacio" : key}
                </button>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
