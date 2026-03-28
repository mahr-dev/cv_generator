import { cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const distBrowser = join(root, "service", "frontend", "dist", "frontend", "browser");
const pub = join(root, "public");

if (!existsSync(distBrowser)) {
  console.error(
    "No existe la carpeta de build de Angular:",
    distBrowser,
    "\nEjecuta antes: cd service/frontend && npm run build",
  );
  process.exit(1);
}

rmSync(pub, { recursive: true, force: true });
mkdirSync(pub, { recursive: true });
cpSync(distBrowser, pub, { recursive: true });
console.log("Copiado Angular -> public/");
