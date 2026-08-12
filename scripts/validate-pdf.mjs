import { readFile, stat } from "node:fs/promises";
import { resolve } from "node:path";
import { PDFDocument, PDFName } from "pdf-lib";

const root = resolve(import.meta.dirname, "..");
const path = resolve(root, "portfolio/pdf/part4-azure-data-engineering-portfolio.pdf");
const bytes = await readFile(path);
const pdf = await PDFDocument.load(bytes, { updateMetadata: false });
const info = await stat(path);

if (pdf.getPageCount() !== 32) throw new Error(`Expected 32 pages; found ${pdf.getPageCount()}.`);
if (pdf.getAuthor() !== "Michael Seth Williams") throw new Error("PDF author metadata is incorrect.");
if (pdf.getSubject() !== "Azure Data Engineering Portfolio") throw new Error("PDF subject metadata is incorrect.");
if (!pdf.getTitle()?.startsWith("Quality-Critical Azure Lakehouse")) throw new Error("PDF title metadata is incorrect.");
if (!pdf.catalog.get(PDFName.of("Outlines"))) throw new Error("PDF bookmarks are missing.");
if (info.size >= 100 * 1024 * 1024) throw new Error("PDF exceeds the 100 MB publication limit.");

for (const [index, page] of pdf.getPages().entries()) {
  const { width, height } = page.getSize();
  if (width !== 648 || height !== 810) throw new Error(`Page ${index + 1} has inconsistent dimensions.`);
}

console.log(`Validated 32 pages, bookmarks, metadata, dimensions, and ${(info.size / 1024 / 1024).toFixed(2)} MB size.`);
