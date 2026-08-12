import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { basename, resolve } from "node:path";
import sharp from "sharp";

const root = resolve(import.meta.dirname, "..");
const architectureDir = resolve(root, "portfolio/architecture");
const svgPath = resolve(architectureDir, "quality-critical-lakehouse.svg");
const content = JSON.parse(await readFile(resolve(root, "portfolio/content/project.json"), "utf8"));
let svg = await readFile(svgPath, "utf8");

if (!svg.includes(content.project.title)) {
  throw new Error("Architecture title is not synchronized with the public content model.");
}

const iconPattern = /href="icons\/([^"]+\.svg)"/g;
const icons = [...svg.matchAll(iconPattern)].map((match) => match[1]);
for (const icon of [...new Set(icons)]) {
  const bytes = await readFile(resolve(architectureDir, "icons", basename(icon)));
  const dataUri = `data:image/svg+xml;base64,${bytes.toString("base64")}`;
  svg = svg.replaceAll(`href="icons/${icon}"`, `href="${dataUri}"`);
}

const png = await sharp(Buffer.from(svg))
  .resize({ width: 2400, withoutEnlargement: false })
  .png({ compressionLevel: 6, adaptiveFiltering: true })
  .toBuffer();

const output = resolve(architectureDir, "quality-critical-lakehouse.png");
const evidenceOutput = resolve(root, "evidence/public/screenshots/01-architecture.png");
await writeFile(output, png);
await mkdir(resolve(root, "evidence/public/screenshots"), { recursive: true });
await copyFile(output, evidenceOutput);
console.log(`Built architecture PNG (${png.length.toLocaleString()} bytes) from official service icons.`);
