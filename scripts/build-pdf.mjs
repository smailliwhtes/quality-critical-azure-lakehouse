import { access, mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import {
  PDFDocument,
  PDFHexString,
  PDFName,
  StandardFonts,
  rgb,
} from "pdf-lib";

const root = resolve(import.meta.dirname, "..");
const content = JSON.parse(await readFile(resolve(root, "portfolio/content/project.json"), "utf8"));
const outputPath = resolve(root, "portfolio/pdf/part4-azure-data-engineering-portfolio.pdf");
const screenshotsDir = resolve(root, "evidence/public/screenshots");
const architecturePath = resolve(root, "portfolio/architecture/quality-critical-lakehouse.png");
const pageWidth = 648;
const pageHeight = 810;

const palette = {
  background: rgb(7 / 255, 19 / 255, 34 / 255),
  panel: rgb(14 / 255, 35 / 255, 56 / 255),
  panel2: rgb(18 / 255, 45 / 255, 70 / 255),
  border: rgb(45 / 255, 78 / 255, 105 / 255),
  white: rgb(246 / 255, 250 / 255, 254 / 255),
  muted: rgb(157 / 255, 178 / 255, 201 / 255),
  blue: rgb(81 / 255, 168 / 255, 1),
  teal: rgb(69 / 255, 220 / 255, 195 / 255),
  amber: rgb(238 / 255, 184 / 255, 84 / 255),
  slate: rgb(128 / 255, 151 / 255, 174 / 255),
};

function wrapText(text, font, size, maxWidth) {
  const words = text.split(/\s+/);
  const lines = [];
  let line = "";
  for (const word of words) {
    const candidate = line ? `${line} ${word}` : word;
    if (font.widthOfTextAtSize(candidate, size) <= maxWidth) line = candidate;
    else {
      if (line) lines.push(line);
      line = word;
    }
  }
  if (line) lines.push(line);
  return lines;
}

function drawWrapped(page, text, { x, top, font, size, color, maxWidth, lineHeight = size * 1.3, maxLines = 5 }) {
  const lines = wrapText(text, font, size, maxWidth).slice(0, maxLines);
  lines.forEach((line, index) => page.drawText(line, { x, y: pageHeight - top - size - index * lineHeight, size, font, color }));
  return top + lines.length * lineHeight;
}

function statusColor(status) {
  if (status === "VERIFIED") return palette.teal;
  if (status === "DEMONSTRATED") return palette.blue;
  return palette.amber;
}

function drawStatus(page, status, bold, x = 52, top = 159) {
  const width = bold.widthOfTextAtSize(status, 8.5) + 24;
  page.drawRectangle({ x, y: pageHeight - top - 24, width, height: 24, borderWidth: 1, borderColor: statusColor(status), color: palette.panel2, opacity: 0.98 });
  page.drawText(status, { x: x + 12, y: pageHeight - top - 16.5, font: bold, size: 8.5, color: statusColor(status) });
}

function drawHeader(page, item, index, fonts) {
  page.drawRectangle({ x: 0, y: 0, width: pageWidth, height: pageHeight, color: palette.background });
  page.drawRectangle({ x: 0, y: pageHeight - 6, width: pageWidth, height: 6, color: index % 2 ? palette.blue : palette.teal });
  page.drawText(item.eyebrow, { x: 52, y: pageHeight - 54, font: fonts.bold, size: 9, color: index % 2 ? palette.blue : palette.teal, characterSpacing: 1.4 });
  drawWrapped(page, item.title, { x: 52, top: 69, font: fonts.bold, size: 27, color: palette.white, maxWidth: 544, lineHeight: 32, maxLines: 2 });
  drawStatus(page, item.status, fonts.bold);
  drawWrapped(page, item.statement, { x: 52, top: 198, font: fonts.regular, size: 13, color: palette.muted, maxWidth: 544, lineHeight: 19, maxLines: 4 });
}

function drawEvidenceFrame(page, item, fonts, index) {
  const x = 52;
  const y = 178;
  const width = 544;
  const height = 330;
  page.drawRectangle({ x, y, width, height, color: palette.panel, borderColor: palette.border, borderWidth: 1 });
  page.drawRectangle({ x: x + 18, y: y + height - 52, width: width - 36, height: 1, color: palette.border });
  page.drawText(item.status === "PRODUCTION_BLUEPRINT" ? "EXECUTION EVIDENCE PENDING" : "IMPLEMENTATION EVIDENCE", { x: x + 22, y: y + height - 35, font: fonts.bold, size: 9, color: statusColor(item.status), characterSpacing: 1 });

  const labels = item.id === "capability-map"
    ? content.capabilities.slice(0, 9)
    : item.id === "gold"
      ? content.gold_objects.map((object) => object.name)
      : ["IMPLEMENTATION", "VALIDATION", "EXECUTION RECEIPT"];

  if (labels.length > 3) {
    labels.forEach((label, i) => {
      const col = i % 3;
      const row = Math.floor(i / 3);
      const cardX = x + 22 + col * 168;
      const cardY = y + 188 - row * 72;
      page.drawRectangle({ x: cardX, y: cardY, width: 150, height: 54, color: palette.panel2, borderColor: palette.border, borderWidth: 0.7 });
      drawWrapped(page, label, { x: cardX + 12, top: pageHeight - cardY - 10, font: fonts.bold, size: 8.8, color: palette.white, maxWidth: 126, lineHeight: 11.5, maxLines: 3 });
    });
  } else {
    labels.forEach((label, i) => {
      const cardX = x + 22 + i * 168;
      page.drawRectangle({ x: cardX, y: y + 117, width: 150, height: 116, color: palette.panel2, borderColor: palette.border, borderWidth: 0.8 });
      page.drawCircle({ x: cardX + 25, y: y + 204, size: 9, color: i === 0 ? palette.blue : i === 1 ? palette.teal : statusColor(item.status) });
      page.drawText(label, { x: cardX + 16, y: y + 172, font: fonts.bold, size: 8.5, color: palette.white });
      const body = i === 0
        ? "Code and configuration point to the exact engineering path."
        : i === 1
          ? "Tests and reconciliation define what must be true."
          : item.status === "PRODUCTION_BLUEPRINT"
            ? "The platform artifact will promote this claim only after execution."
            : "The deterministic artifact is available for inspection.";
      drawWrapped(page, body, { x: cardX + 16, top: pageHeight - (y + 157), font: fonts.regular, size: 8.5, color: palette.muted, maxWidth: 118, lineHeight: 12, maxLines: 5 });
    });
  }

  page.drawText(`CONTROLLED SEED ${content.project.seed}`, { x: x + 22, y: y + 31, font: fonts.bold, size: 8.5, color: palette.slate, characterSpacing: .7 });
  page.drawText(`${String(index + 1).padStart(2, "0")} / 32`, { x: x + width - 62, y: y + 31, font: fonts.bold, size: 8.5, color: palette.slate });
}

async function maybeEmbedScreenshot(pdf, item) {
  let path;
  if (item.id === "architecture" || item.id === "cover") path = architecturePath;
  else if (item.screenshot) path = resolve(screenshotsDir, item.screenshot);
  else return null;
  try {
    await access(path);
    const bytes = await readFile(path);
    return path.toLowerCase().endsWith(".jpg") || path.toLowerCase().endsWith(".jpeg")
      ? await pdf.embedJpg(bytes)
      : await pdf.embedPng(bytes);
  } catch {
    return null;
  }
}

function drawImageFrame(page, image) {
  const frame = { x: 52, y: 151, width: 544, height: 356 };
  page.drawRectangle({ ...frame, color: palette.panel, borderColor: palette.border, borderWidth: 1 });
  const natural = image.scale(1);
  const scale = Math.min((frame.width - 18) / natural.width, (frame.height - 18) / natural.height);
  const width = natural.width * scale;
  const height = natural.height * scale;
  page.drawImage(image, { x: frame.x + (frame.width - width) / 2, y: frame.y + (frame.height - height) / 2, width, height });
}

function drawFooter(page, index, fonts) {
  page.drawLine({ start: { x: 52, y: 91 }, end: { x: 596, y: 91 }, thickness: 0.7, color: palette.border });
  page.drawText("MICHAEL SETH WILLIAMS", { x: 52, y: 65, font: fonts.bold, size: 8, color: palette.slate, characterSpacing: 1.2 });
  page.drawText("QUALITY-CRITICAL AZURE LAKEHOUSE", { x: 52, y: 47, font: fonts.regular, size: 7.7, color: palette.slate, characterSpacing: .5 });
  page.drawText(String(index + 1).padStart(2, "0"), { x: 576, y: 52, font: fonts.bold, size: 11, color: index % 2 ? palette.blue : palette.teal });
}

function addOutlines(pdf, pages, items) {
  const context = pdf.context;
  const outlineRef = context.nextRef();
  const itemRefs = items.map(() => context.nextRef());
  const outline = context.obj({ Type: "Outlines", First: itemRefs[0], Last: itemRefs.at(-1), Count: itemRefs.length });
  context.assign(outlineRef, outline);
  itemRefs.forEach((ref, index) => {
    const dict = {
      Title: PDFHexString.fromText(`${String(index + 1).padStart(2, "0")} ${items[index].title}`),
      Parent: outlineRef,
      Dest: [pages[index].ref, PDFName.of("Fit")],
    };
    if (index > 0) dict.Prev = itemRefs[index - 1];
    if (index < itemRefs.length - 1) dict.Next = itemRefs[index + 1];
    context.assign(ref, context.obj(dict));
  });
  pdf.catalog.set(PDFName.of("Outlines"), outlineRef);
  pdf.catalog.set(PDFName.of("PageMode"), PDFName.of("UseOutlines"));
}

if (content.pdf_pages.length !== 32) throw new Error("The shared content model must define exactly 32 pages.");

const pdf = await PDFDocument.create();
pdf.setTitle(`${content.project.title}: ${content.project.subtitle}`);
pdf.setAuthor(content.project.author);
pdf.setSubject("Azure Data Engineering Portfolio");
pdf.setKeywords(["Azure Data Engineering", "Azure Databricks", "PySpark", "Delta Lake", "Lakeflow", "Unity Catalog"]);
pdf.setCreator(content.project.author);
pdf.setProducer(content.project.title);
pdf.setCreationDate(new Date("2026-08-12T00:00:00Z"));
pdf.setModificationDate(new Date("2026-08-12T00:00:00Z"));

const fonts = {
  regular: await pdf.embedFont(StandardFonts.Helvetica),
  bold: await pdf.embedFont(StandardFonts.HelveticaBold),
};
const pages = [];

for (const [index, item] of content.pdf_pages.entries()) {
  const page = pdf.addPage([pageWidth, pageHeight]);
  pages.push(page);
  drawHeader(page, item, index, fonts);
  const screenshot = await maybeEmbedScreenshot(pdf, item);
  if (screenshot) drawImageFrame(page, screenshot);
  else drawEvidenceFrame(page, item, fonts, index);

  if (item.id === "repository") {
    page.drawRectangle({ x: 52, y: 108, width: 544, height: 30, color: palette.panel2, borderColor: palette.blue, borderWidth: 0.8 });
    page.drawText(content.project.site, { x: 68, y: 119, font: fonts.bold, size: 9, color: palette.blue });
  }
  drawFooter(page, index, fonts);
}

addOutlines(pdf, pages, content.pdf_pages);
await mkdir(resolve(root, "portfolio/pdf"), { recursive: true });
const bytes = await pdf.save({ useObjectStreams: false });
await writeFile(outputPath, bytes);
console.log(`Built 32-page portfolio document (${bytes.length.toLocaleString()} bytes).`);
