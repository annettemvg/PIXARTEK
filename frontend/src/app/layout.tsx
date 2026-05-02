import type { Metadata } from "next";
import { Nunito, Bricolage_Grotesque } from "next/font/google";
import "./globals.css";

const display = Bricolage_Grotesque({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["400", "500", "600", "700", "800"],
  display: "swap",
});

const body = Nunito({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600", "700", "800"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "PIXARTEK — Tu Estudio de Arte",
  description: "Robot Educativo de Pintura Artística",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className={`${display.variable} ${body.variable} font-body bg-pixartek-cream text-pixartek-ink min-h-screen`}>
        {children}
      </body>
    </html>
  );
}
