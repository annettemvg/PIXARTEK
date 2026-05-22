"use client";

interface Props {
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
}

const sizes = {
  sm: { h: 32,  fontSize: 22 },
  md: { h: 52,  fontSize: 36 },
  lg: { h: 80,  fontSize: 56 },
  xl: { h: 120, fontSize: 84 },
};

// Each letter carries its own paint color from the Bidó-inspired palette
const LETTERS = [
  { ch: "p", color: "#E07B6A" },  // coral
  { ch: "i", color: "#D4956A" },  // warm orange
  { ch: "x", color: "#D4B85A" },  // golden yellow
  { ch: "a", color: "#7DC4A8" },  // mint
  { ch: "r", color: "#6BACC0" },  // teal
  { ch: "t", color: "#7096BC" },  // periwinkle blue
  { ch: "e", color: "#A495C0" },  // lavender
  { ch: "k", color: "#D498B8" },  // blush pink
];

export default function PixartekLogo({ size = "md", className = "" }: Props) {
  const { h, fontSize } = sizes[size];
  const letterSpacing = fontSize * 0.62;
  const totalWidth = LETTERS.length * letterSpacing + fontSize * 0.4;

  return (
    <svg
      viewBox={`0 0 ${totalWidth} ${h + 8}`}
      height={h}
      aria-label="pixartek"
      className={className}
      style={{ overflow: "visible" }}
    >
      <defs>
        {/* Painterly texture filter */}
        <filter id="paint-texture" x="-5%" y="-5%" width="110%" height="110%">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.055"
            numOctaves="3"
            seed="2"
            result="noise"
          />
          <feDisplacementMap
            in="SourceGraphic"
            in2="noise"
            scale={fontSize * 0.18}
            xChannelSelector="R"
            yChannelSelector="G"
            result="displaced"
          />
          <feGaussianBlur in="displaced" stdDeviation="0.4" result="blurred" />
          <feComposite in="blurred" in2="SourceGraphic" operator="atop" />
        </filter>
        {/* Subtle drop shadow */}
        <filter id="letter-shadow" x="-10%" y="-10%" width="120%" height="120%">
          <feDropShadow dx="1" dy="2" stdDeviation="2" floodOpacity="0.12" />
        </filter>
      </defs>

      {LETTERS.map(({ ch, color }, i) => {
        const x = i * letterSpacing + fontSize * 0.05;
        const y = h * 0.82;
        return (
          <g key={i} filter="url(#paint-texture)">
            <text
              x={x}
              y={y}
              fontSize={fontSize}
              fontFamily="'Bricolage Grotesque', 'Nunito', sans-serif"
              fontWeight="800"
              fill={color}
              letterSpacing={0}
              style={{ paintOrder: "stroke fill" }}
            >
              {ch}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
