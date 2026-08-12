import { readdir, readFile } from "node:fs/promises";
import { extname, relative, resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const excluded = new Set([".git", ".tools", ".venv", "node_modules", "dist", "rendered"]);
const textual = new Set([".md", ".json", ".html", ".css", ".ts", ".js", ".mjs", ".py", ".yml", ".yaml", ".bicep", ".ps1", ".toml", ".sql", ".txt", ".svg"]);
const terms = [
  ["chat", "gpt"].join(""),
  ["open", "ai"].join(""),
  ["co", "dex"].join(""),
  ["standalone ", "llm"].join(""),
  ["large language ", "model"].join(""),
  ["generated ", "by"].join(""),
  ["co-authored", "-by"].join(""),
];

async function walk(directory) {
  const files = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (excluded.has(entry.name)) continue;
    const path = resolve(directory, entry.name);
    if (entry.isDirectory()) files.push(...await walk(path));
    else if (textual.has(extname(entry.name).toLowerCase())) files.push(path);
  }
  return files;
}

const hits = [];
for (const file of await walk(root)) {
  const text = (await readFile(file, "utf8")).toLowerCase();
  for (const term of terms) {
    if (text.includes(term)) hits.push(`${relative(root, file)}: disallowed publication attribution`);
  }
}

if (hits.length) {
  console.error(hits.join("\n"));
  process.exit(1);
}
console.log("Publication attribution scan passed with zero hits.");
