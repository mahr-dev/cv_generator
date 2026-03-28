/**
 * - API_PUBLIC_URL definida → apiUrl = URL del backend (llamada directa, CORS en API).
 * - Sin API_PUBLIC_URL → apiUrl = '' (rutas relativas /api/...; proxy en vercel.json).
 *
 * Tras desplegar el backend en Vercel, sustituye en vercel.json la URL del rewrite
 * "destination" (o define API_PUBLIC_URL y omite el proxy).
 */
const fs = require("fs");
const path = require("path");

const envDir = path.join(__dirname, "..", "src", "environments");
const out = path.join(envDir, "environment.vercel.generated.ts");

const raw = (process.env.API_PUBLIC_URL || "").trim().replace(/\/$/, "");

const body = raw
  ? `/* Generado: API_PUBLIC_URL (llamada directa al backend) */
export const environment = {
  production: true,
  apiUrl: ${JSON.stringify(raw)},
};
`
  : `/* Generado: proxy /api → backend (ver service/frontend/vercel.json, destination con /api/:path*) */
export const environment = {
  production: true,
  apiUrl: '',
};
`;

fs.writeFileSync(out, body, "utf8");
console.log(raw ? `API_PUBLIC_URL -> ${raw}` : "apiUrl -> '' (proxy /api/...)");
