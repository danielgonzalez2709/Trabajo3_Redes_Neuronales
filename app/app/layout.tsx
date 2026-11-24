import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Operación inteligente de transporte",
  description:
    "Herramienta académica: pronóstico de demanda y flota, detección de conducción distractiva y recomendación de destinos, con modelos que corren en el navegador.",
};

export const viewport: Viewport = { width: "device-width", initialScale: 1, themeColor: "#fbe8cc" };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
