import { copyFile, cp, mkdir } from "node:fs/promises";
import { resolve } from "node:path";
import { defineConfig } from "vite";

const root = resolve(import.meta.dirname, "portfolio/site");
const outDir = resolve(root, "dist");

export default defineConfig({
  root,
  base: "/quality-critical-azure-lakehouse/",
  publicDir: false,
  build: {
    outDir,
    emptyOutDir: true,
    sourcemap: false,
    target: "es2022",
  },
  plugins: [
    {
      name: "copy-portfolio-evidence",
      async closeBundle() {
        await mkdir(resolve(outDir, "assets/architecture"), { recursive: true });
        await mkdir(resolve(outDir, "downloads"), { recursive: true });
        await cp(resolve(import.meta.dirname, "portfolio/architecture/icons"), resolve(outDir, "assets/architecture/icons"), { recursive: true });
        await copyFile(resolve(import.meta.dirname, "portfolio/architecture/quality-critical-lakehouse.svg"), resolve(outDir, "assets/architecture/quality-critical-lakehouse.svg"));
        await copyFile(resolve(import.meta.dirname, "portfolio/architecture/quality-critical-lakehouse.png"), resolve(outDir, "assets/architecture/quality-critical-lakehouse.png"));
        await copyFile(resolve(import.meta.dirname, "portfolio/pdf/part4-azure-data-engineering-portfolio.pdf"), resolve(outDir, "downloads/part4-azure-data-engineering-portfolio.pdf"));
        await cp(resolve(import.meta.dirname, "evidence/public"), resolve(outDir, "evidence"), { recursive: true });
      },
    },
  ],
});
