/**
 * Si defines CVGEN_API_BASE en Vercel (proyecto solo frontend), inyecta la URL del API
 * antes de `ng build`. Vacío = mismo origen o lógica localhost en app.ts.
 */
import { writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const out = join(root, "src", "generated-api-base.ts");
const base = (process.env.CVGEN_API_BASE ?? "").trim();
const escaped = JSON.stringify(base);
writeFileSync(
  out,
  `/* Generado por scripts/write-api-base.mjs — no editar a mano */\nexport const API_BASE_URL: string = ${escaped};\n`,
);
console.log("write-api-base:", base ? `API_BASE_URL = ${base}` : "API_BASE_URL = '' (mismo origen / dev)");
