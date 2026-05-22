import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        pixartek: {
          cream:    "#F5F2EE",
          white:    "#FFFFFF",
          ink:      "#1A1818",
          muted:    "#6B6866",
          border:   "#E8E4DE",
          coral:    "#E07B6A",
          yellow:   "#D4B85A",
          mint:     "#7DC4A8",
          sky:      "#7096BC",
          lavender: "#A495C0",
          blush:    "#D498B8",
          // legacy aliases kept for session page
          primary:  "#F5F2EE",
          accent:   "#E07B6A",
          canvas:   "#F5F2EE",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "sans-serif"],
        body:    ["var(--font-body)",    "sans-serif"],
      },
      keyframes: {
        fadeUp: {
          "0%":   { opacity: "0", transform: "translateY(24px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeIn: {
          "0%":   { opacity: "0" },
          "100%": { opacity: "1" },
        },
        scaleIn: {
          "0%":   { opacity: "0", transform: "scale(0.92)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        shimmer: {
          "0%":   { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        "fade-up":  "fadeUp 0.5s ease forwards",
        "fade-in":  "fadeIn 0.4s ease forwards",
        "scale-in": "scaleIn 0.4s ease forwards",
        shimmer:    "shimmer 1.6s linear infinite",
      },
      boxShadow: {
        card:  "0 2px 16px 0 rgba(0,0,0,0.07)",
        hover: "0 8px 32px 0 rgba(0,0,0,0.12)",
        btn:   "0 4px 16px 0 rgba(224,123,106,0.35)",
      },
    },
  },
  plugins: [],
};

export default config;
