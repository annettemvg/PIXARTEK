"use client";

export type PixiMood = "idle" | "listening" | "thinking" | "speaking" | "happy" | "surprised" | "celebrating";

interface Props {
  mood: PixiMood;
  size?: number;
}

export default function PixiAvatar({ mood, size = 56 }: Props) {
  const eyeAnimation = mood === "listening" ? "animate-pulse" : "";
  const isHappy = mood === "happy" || mood === "celebrating";
  const isSurprised = mood === "surprised";
  const isThinking = mood === "thinking";
  const isSpeaking = mood === "speaking";

  return (
    <div
      className="relative shrink-0"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} viewBox="0 0 56 56" fill="none" xmlns="http://www.w3.org/2000/svg">
        {/* Face circle */}
        <circle cx="28" cy="28" r="26"
          fill={mood === "celebrating" ? "#FFD97D" : mood === "thinking" ? "#C8E6FF" : "#FFE8D6"}
          className={mood === "celebrating" ? "animate-bounce" : ""}
        />

        {/* Left eye */}
        <g className={eyeAnimation}>
          {isSurprised ? (
            <circle cx="20" cy="23" r="5" fill="#2D2D2D" />
          ) : isThinking ? (
            <ellipse cx="20" cy="24" rx="4" ry="3" fill="#2D2D2D" />
          ) : (
            <ellipse cx="20" cy={mood === "happy" || mood === "celebrating" ? "25" : "23"} rx="4" ry={isHappy ? "3" : "4"} fill="#2D2D2D" />
          )}
          {/* Eye shine */}
          <circle cx="22" cy={isSurprised ? "21" : "21"} r="1.5" fill="white" />
        </g>

        {/* Right eye */}
        <g className={eyeAnimation}>
          {isSurprised ? (
            <circle cx="36" cy="23" r="5" fill="#2D2D2D" />
          ) : isThinking ? (
            <ellipse cx="36" cy="24" rx="4" ry="3" fill="#2D2D2D" />
          ) : (
            <ellipse cx="36" cy={isHappy ? "25" : "23"} rx="4" ry={isHappy ? "3" : "4"} fill="#2D2D2D" />
          )}
          <circle cx="38" cy="21" r="1.5" fill="white" />
        </g>

        {/* Blink layer — idle random */}
        {mood === "idle" && (
          <g className="opacity-0 hover:opacity-100">
            <rect x="16" y="21" width="8" height="3" rx="1.5" fill="#2D2D2D" />
            <rect x="32" y="21" width="8" height="3" rx="1.5" fill="#2D2D2D" />
          </g>
        )}

        {/* Mouth */}
        {isHappy && (
          <path d="M18 35 Q28 44 38 35" stroke="#2D2D2D" strokeWidth="2.5" strokeLinecap="round" fill="none" />
        )}
        {isSurprised && (
          <ellipse cx="28" cy="38" rx="6" ry="5" fill="#2D2D2D" />
        )}
        {isThinking && (
          <path d="M20 37 Q28 34 36 37" stroke="#2D2D2D" strokeWidth="2" strokeLinecap="round" fill="none" />
        )}
        {isSpeaking && (
          <ellipse cx="28" cy="37" rx="7" ry="4" fill="#2D2D2D" className="animate-pulse" />
        )}
        {mood === "idle" && (
          <path d="M20 36 Q28 40 36 36" stroke="#2D2D2D" strokeWidth="2" strokeLinecap="round" fill="none" />
        )}
        {mood === "listening" && (
          <path d="M20 36 Q28 40 36 36" stroke="#2D2D2D" strokeWidth="2" strokeLinecap="round" fill="none" />
        )}

        {/* Thinking dots */}
        {isThinking && (
          <>
            <circle cx="40" cy="18" r="2" fill="#79C4BE" className="animate-bounce" style={{ animationDelay: "0ms" }} />
            <circle cx="44" cy="14" r="1.5" fill="#79C4BE" className="animate-bounce" style={{ animationDelay: "150ms" }} />
            <circle cx="47" cy="10" r="1" fill="#79C4BE" className="animate-bounce" style={{ animationDelay: "300ms" }} />
          </>
        )}

        {/* Listening mic indicator */}
        {mood === "listening" && (
          <circle cx="28" cy="28" r="26" stroke="#79C4BE" strokeWidth="2" fill="none" className="animate-ping opacity-30" />
        )}

        {/* Cheeks when happy */}
        {isHappy && (
          <>
            <circle cx="15" cy="32" r="5" fill="#FFB3A7" opacity="0.5" />
            <circle cx="41" cy="32" r="5" fill="#FFB3A7" opacity="0.5" />
          </>
        )}

        {/* Beret / artist hat */}
        <ellipse cx="28" cy="6" rx="14" ry="5" fill="#E07B6A" />
        <circle cx="36" cy="4" r="3" fill="#C45A4A" />
        <ellipse cx="28" cy="10" rx="16" ry="4" fill="#E07B6A" />
      </svg>

      {/* Celebrating stars */}
      {mood === "celebrating" && (
        <div className="absolute inset-0 pointer-events-none">
          <span className="absolute top-0 right-0 text-xs animate-bounce" style={{ animationDelay: "0ms" }}>⭐</span>
          <span className="absolute bottom-0 left-0 text-xs animate-bounce" style={{ animationDelay: "200ms" }}>✨</span>
        </div>
      )}
    </div>
  );
}
