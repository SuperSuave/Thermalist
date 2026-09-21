import fs from "fs";
import path from "path";

export interface LabelThemeDefinition {
  value: string;
  label: string;
}

export const LABEL_THEMES: LabelThemeDefinition[] = [
  { value: "framed_food", label: "Framed Food (default)" },
  { value: "minimal", label: "Minimal (top/bottom lines only)" },
  { value: "compact", label: "Compact" },
  { value: "bold", label: "Bold (thick frame)" },
  { value: "playful", label: "Playful (rounded, softer)" },
  { value: "reminders_notebook", label: "Reminders Notebook" },
];

export interface LabelRenderData {
  verb?: string;
  date?: string;
  note?: string;
  subtext?: string;
}

function escapeXml(unsafe: string): string {
  return (unsafe || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export function generateLabelSvg(data: LabelRenderData, themeName = "framed_food", bw = false): string {
  const verb = escapeXml((data.verb || "Opened").toUpperCase());
  const date = escapeXml(data.date || new Date().toLocaleDateString("en-US", { month: "2-digit", day: "2-digit", year: "2-digit" }));
  const note = escapeXml(data.note || "");

  const width = 640;
  const height = 360;

  const bg = bw ? "#ffffff" : "#fdfbf7";
  const ink = "#000000";
  const pillBg = ink;
  const pillText = bg;

  if (themeName === "minimal") {
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">
  <rect width="${width}" height="${height}" fill="${bg}" />
  <line x1="28" y1="28" x2="${width - 28}" y2="28" stroke="${ink}" stroke-width="4" stroke-linecap="round" />
  
  <!-- Header with verb and date -->
  <rect x="36" y="48" width="160" height="44" rx="8" fill="${pillBg}" />
  <text x="116" y="78" fill="${pillText}" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="800" text-anchor="middle" letter-spacing="2">${verb}</text>
  <text x="${width - 40}" y="80" fill="${ink}" font-family="monospace, sans-serif" font-size="34" font-weight="700" text-anchor="end">${date}</text>
  
  <line x1="36" y1="112" x2="${width - 36}" y2="112" stroke="${ink}" stroke-width="2" stroke-dasharray="4,4" />
  
  <!-- Note Content -->
  <text x="36" y="180" fill="${ink}" font-family="system-ui, -apple-system, sans-serif" font-size="44" font-weight="700">${note || "Kitchen Label"}</text>
  
  <line x1="28" y1="${height - 28}" x2="${width - 28}" y2="${height - 28}" stroke="${ink}" stroke-width="4" stroke-linecap="round" />
</svg>`;
  }

  if (themeName === "bold") {
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">
  <rect width="${width}" height="${height}" fill="${bg}" />
  <rect x="20" y="20" width="${width - 40}" height="${height - 40}" rx="12" fill="none" stroke="${ink}" stroke-width="8" />
  
  <!-- Header Bar -->
  <rect x="24" y="24" width="${width - 48}" height="84" fill="${ink}" />
  <text x="44" y="80" fill="${pillText}" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="900" letter-spacing="3">${verb}</text>
  <text x="${width - 44}" y="80" fill="${pillText}" font-family="system-ui, -apple-system, sans-serif" font-size="38" font-weight="800" text-anchor="end">${date}</text>
  
  <!-- Note Content -->
  <text x="44" y="195" fill="${ink}" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="800">${note || "Kitchen Label"}</text>
</svg>`;
  }

  if (themeName === "playful") {
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">
  <rect width="${width}" height="${height}" fill="${bg}" />
  <rect x="22" y="22" width="${width - 44}" height="${height - 44}" rx="32" fill="none" stroke="${ink}" stroke-width="4" />
  
  <!-- Header -->
  <rect x="44" y="44" width="180" height="52" rx="26" fill="${pillBg}" />
  <text x="134" y="79" fill="${pillText}" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="800" text-anchor="middle" letter-spacing="2">${verb}</text>
  <text x="${width - 48}" y="82" fill="${ink}" font-family="system-ui, -apple-system, sans-serif" font-size="34" font-weight="700" text-anchor="end">${date}</text>
  
  <path d="M 44 116 Q 180 126, 320 116 T 596 116" fill="none" stroke="${ink}" stroke-width="2" />
  
  <!-- Note Content -->
  <text x="48" y="195" fill="${ink}" font-family="system-ui, -apple-system, sans-serif" font-size="42" font-weight="700">${note || "Kitchen Label"}</text>
</svg>`;
  }

  if (themeName === "reminders_notebook") {
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">
  <rect width="${width}" height="${height}" fill="${bg}" />
  <rect x="24" y="20" width="${width - 48}" height="${height - 40}" rx="14" fill="none" stroke="${ink}" stroke-width="3" />
  
  <!-- Header with notebook spiral hint -->
  <circle cx="50" cy="54" r="8" fill="none" stroke="${ink}" stroke-width="2.5" />
  <circle cx="80" cy="54" r="8" fill="none" stroke="${ink}" stroke-width="2.5" />
  <circle cx="110" cy="54" r="8" fill="none" stroke="${ink}" stroke-width="2.5" />
  
  <text x="144" y="62" fill="${ink}" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="800" letter-spacing="1">${verb}</text>
  <text x="${width - 48}" y="62" fill="${ink}" font-family="monospace, sans-serif" font-size="26" font-weight="700" text-anchor="end">${date}</text>
  
  <!-- Notebook lines -->
  <line x1="40" y1="100" x2="${width - 40}" y2="100" stroke="${ink}" stroke-width="2" />
  
  <!-- Checkbox + Note -->
  <rect x="46" y="145" width="28" height="28" rx="6" fill="none" stroke="${ink}" stroke-width="3" />
  <text x="90" y="170" fill="${ink}" font-family="system-ui, -apple-system, sans-serif" font-size="36" font-weight="700">${note || "Item note"}</text>
  
  <line x1="40" y1="210" x2="${width - 40}" y2="210" stroke="${ink}" stroke-width="1.5" stroke-dasharray="6,4" />
  <line x1="40" y1="260" x2="${width - 40}" y2="260" stroke="${ink}" stroke-width="1.5" stroke-dasharray="6,4" />
</svg>`;
  }

  // Default: framed_food
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">
  <rect width="${width}" height="${height}" fill="${bg}" />
  <rect x="22" y="22" width="${width - 44}" height="${height - 44}" rx="20" fill="none" stroke="${ink}" stroke-width="3.5" />
  
  <!-- Header: pill verb + date -->
  <rect x="42" y="44" width="160" height="46" rx="14" fill="${pillBg}" />
  <text x="122" y="76" fill="${pillText}" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="800" text-anchor="middle" letter-spacing="2">${verb}</text>
  <text x="${width - 46}" y="78" fill="${ink}" font-family="system-ui, -apple-system, sans-serif" font-size="34" font-weight="800" text-anchor="end">${date}</text>
  
  <line x1="42" y1="110" x2="${width - 42}" y2="110" stroke="${ink}" stroke-width="2.5" />
  
  <!-- Note Content -->
  <text x="44" y="185" fill="${ink}" font-family="system-ui, -apple-system, sans-serif" font-size="44" font-weight="700">${note || "Kitchen Label"}</text>
</svg>`;
}

export function renderAndSaveLabel(data: LabelRenderData, themeName = "framed_food"): {
  gray_path: string;
  bw_path: string;
  width: number;
  height: number;
} {
  const imagesDir = path.join(process.cwd(), "generated_images");
  if (!fs.existsSync(imagesDir)) {
    fs.mkdirSync(imagesDir, { recursive: true });
  }

  const graySvg = generateLabelSvg(data, themeName, false);
  const bwSvg = generateLabelSvg(data, themeName, true);

  const grayFile = path.join(imagesDir, "label.svg");
  const bwFile = path.join(imagesDir, "label-bw.svg");

  fs.writeFileSync(grayFile, graySvg, "utf-8");
  fs.writeFileSync(bwFile, bwSvg, "utf-8");

  return {
    gray_path: "/generated_images/label.svg",
    bw_path: "/generated_images/label-bw.svg",
    width: 640,
    height: 360,
  };
}
