import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PIXARTEK — Tu Estudio de Arte",
  description: "Robot Educativo de Pintura Artistica",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="bg-pixartek-cream text-pixartek-ink min-h-screen">
        {children}
      </body>
    </html>
  );
}
