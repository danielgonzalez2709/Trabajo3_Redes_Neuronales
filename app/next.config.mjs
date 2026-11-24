/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export", // sitio estático: sin servidor
  reactStrictMode: true,
  turbopack: { root: import.meta.dirname }, // la raíz es app/ (hay otro package-lock.json más arriba en algunos equipos)
  allowedDevOrigins: ["*.trycloudflare.com"], // solo `next dev`: permite abrir la app por el túnel
};

export default nextConfig;
