import fs from "fs";
import path from "path";

export interface GraphicThemeOptions {
  themeName: string;
  title?: string;
  subtitle?: string;
  dateStr?: string;
  items?: Array<{
    title: string;
    completed?: boolean;
    description?: string;
    due?: string | null;
    labels?: string[];
  }>;
  categories?: Array<{
    name: string;
    items: Array<{
      title: string;
      completed?: boolean;
      description?: string;
      due?: string | null;
      labels?: string[];
    }>;
  }>;
  recipe?: {
    title: string;
    description?: string;
    prepTime?: string;
    cookTime?: string;
    totalTime?: string;
    servings?: string;
    source?: string;
    ingredients: string[];
    instructions: string[];
  };
  noteBody?: string;
}

const PUBLIC_IMAGES_DIR = path.join(process.cwd(), "generated_images");

function escapeXml(unsafe: string): string {
  return String(unsafe || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

function wordWrap(text: string, maxChars: number): string[] {
  if (!text) return [];
  const lines: string[] = [];
  const paragraphs = text.split("\n");
  for (const para of paragraphs) {
    if (!para.trim()) {
      lines.push("");
      continue;
    }
    const words = para.split(/\s+/);
    let cur = "";
    for (const w of words) {
      if (!cur) {
        cur = w;
      } else if ((cur + " " + w).length <= maxChars) {
        cur += " " + w;
      } else {
        lines.push(cur);
        cur = w;
      }
    }
    if (cur) lines.push(cur);
  }
  return lines;
}

export function renderUnboundedGraphicSvg(opts: GraphicThemeOptions): { svg: string; width: number; height: number } {
  const width = 576;
  const theme = opts.themeName || "framed_food";
  const dateStr = opts.dateStr || new Date().toLocaleDateString("en-US", { month: "2-digit", day: "2-digit", year: "2-digit" });

  let curY = 32;
  const elements: string[] = [];

  let fontFamily = "'Courier New', Courier, monospace";
  let displayFont = "'Impact', 'Arial Black', sans-serif";
  let bodyFont = "'Helvetica Neue', Arial, sans-serif";
  let borderStyle = "double";
  let cornerRadius = 0;

  if (theme === "minimal") {
    fontFamily = "'Helvetica Neue', Arial, sans-serif";
    displayFont = "'Helvetica Neue', Arial, sans-serif";
    bodyFont = "'Helvetica Neue', Arial, sans-serif";
  } else if (theme === "bold") {
    fontFamily = "'Impact', 'Arial Black', sans-serif";
    displayFont = "'Impact', 'Arial Black', sans-serif";
    bodyFont = "'Arial Black', Arial, sans-serif";
    borderStyle = "thick";
  } else if (theme === "playful") {
    fontFamily = "'Comic Sans MS', 'Chalkboard SE', sans-serif";
    displayFont = "'Trebuchet MS', sans-serif";
    bodyFont = "'Trebuchet MS', sans-serif";
    cornerRadius = 24;
    borderStyle = "round";
  } else if (theme === "reminders_notebook") {
    fontFamily = "'Georgia', serif";
    displayFont = "'Georgia', serif";
    bodyFont = "'Georgia', serif";
    borderStyle = "notebook";
  }

  const marginX = borderStyle === "notebook" ? 48 : 28;
  const contentWidth = width - marginX * 2;

  if (opts.title) {
    curY += 12;
    if (theme === "bold") {
      const titleLines = wordWrap(opts.title.toUpperCase(), 24);
      const bannerHeight = titleLines.length * 36 + 28;
      elements.push(`<rect x="${marginX}" y="${curY}" width="${contentWidth}" height="${bannerHeight}" fill="#000000" rx="${cornerRadius > 0 ? 8 : 0}" />`);
      let bannerY = curY + 36;
      for (const line of titleLines) {
        elements.push(`<text x="${width / 2}" y="${bannerY}" font-family="${displayFont}" font-size="28" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">${escapeXml(line)}</text>`);
        bannerY += 34;
      }
      curY += bannerHeight + 16;
    } else if (theme === "minimal") {
      elements.push(`<text x="${marginX}" y="${curY + 28}" font-family="${displayFont}" font-size="30" font-weight="700" fill="#000000">${escapeXml(opts.title)}</text>`);
      elements.push(`<text x="${width - marginX}" y="${curY + 28}" font-family="${bodyFont}" font-size="14" fill="#666666" text-anchor="end">${escapeXml(dateStr)}</text>`);
      curY += 42;
      elements.push(`<line x1="${marginX}" y1="${curY}" x2="${width - marginX}" y2="${curY}" stroke="#000000" stroke-width="2" />`);
      curY += 24;
    } else if (theme === "reminders_notebook") {
      elements.push(`<text x="${marginX + 8}" y="${curY + 28}" font-family="${displayFont}" font-size="28" font-style="italic" font-weight="bold" fill="#000000">${escapeXml(opts.title)}</text>`);
      elements.push(`<text x="${width - marginX}" y="${curY + 28}" font-family="${bodyFont}" font-size="14" fill="#555555" text-anchor="end">${escapeXml(dateStr)}</text>`);
      curY += 40;
      elements.push(`<line x1="${marginX}" y1="${curY}" x2="${width - marginX}" y2="${curY}" stroke="#e04040" stroke-width="1.5" />`);
      curY += 20;
    } else {
      const titleLines = wordWrap(opts.title.toUpperCase(), 24);
      let titleY = curY + 28;
      for (const line of titleLines) {
        elements.push(`<text x="${width / 2}" y="${titleY}" font-family="${displayFont}" font-size="28" font-weight="bold" fill="#000000" text-anchor="middle" letter-spacing="2">${escapeXml(line)}</text>`);
        titleY += 32;
      }
      curY = titleY;
      elements.push(`<text x="${width / 2}" y="${curY}" font-family="${bodyFont}" font-size="14" font-weight="bold" fill="#555555" text-anchor="middle" letter-spacing="3">${escapeXml(dateStr)}</text>`);
      curY += 16;
      elements.push(`<line x1="${marginX + 20}" y1="${curY}" x2="${width - marginX - 20}" y2="${curY}" stroke="#000000" stroke-width="2" stroke-dasharray="6,4" />`);
      curY += 24;
    }
  }

  if (opts.subtitle) {
    const subLines = wordWrap(opts.subtitle, 42);
    for (const sline of subLines) {
      elements.push(`<text x="${marginX}" y="${curY}" font-family="${bodyFont}" font-size="14" fill="#555555">${escapeXml(sline)}</text>`);
      curY += 20;
    }
    curY += 10;
  }

  if (opts.noteBody) {
    const lines = wordWrap(opts.noteBody, 36);
    for (const line of lines) {
      if (line === "") {
        curY += 16;
        continue;
      }
      if (borderStyle === "notebook") {
        elements.push(`<line x1="${marginX}" y1="${curY + 4}" x2="${width - marginX}" y2="${curY + 4}" stroke="#d0d8e8" stroke-width="1" />`);
      }
      elements.push(`<text x="${marginX + 4}" y="${curY}" font-family="${bodyFont}" font-size="18" font-weight="500" fill="#111111">${escapeXml(line)}</text>`);
      curY += 28;
    }
    curY += 16;
  }

  const renderTaskList = (taskList: NonNullable<GraphicThemeOptions["items"]>) => {
    for (const item of taskList) {
      const boxSize = 18;
      const boxY = curY - 14;

      if (item.completed) {
        elements.push(`<rect x="${marginX}" y="${boxY}" width="${boxSize}" height="${boxSize}" fill="#000000" stroke="#000000" stroke-width="1.5" rx="3" />`);
        elements.push(`<path d="M ${marginX + 4} ${boxY + 9} L ${marginX + 8} ${boxY + 14} L ${marginX + 15} ${boxY + 4}" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />`);
      } else {
        elements.push(`<rect x="${marginX}" y="${boxY}" width="${boxSize}" height="${boxSize}" fill="#ffffff" stroke="#000000" stroke-width="1.8" rx="3" />`);
      }

      const textX = marginX + boxSize + 12;
      const itemTitleLines = wordWrap(item.title, 32);

      let itemY = curY;
      for (const textLine of itemTitleLines) {
        const isCrossed = item.completed;
        elements.push(`<text x="${textX}" y="${itemY}" font-family="${bodyFont}" font-size="17" font-weight="${item.completed ? "normal" : "600"}" fill="${item.completed ? "#777777" : "#111111"}" ${isCrossed ? 'text-decoration="line-through"' : ""}>${escapeXml(textLine)}</text>`);
        itemY += 22;
      }
      curY = itemY;

      if (item.description || item.due || (item.labels && item.labels.length > 0)) {
        let tagLine = "";
        if (item.due) tagLine += `Due: ${item.due}  `;
        if (item.labels && item.labels.length > 0) tagLine += `[${item.labels.join(", ")}]`;

        if (tagLine) {
          elements.push(`<text x="${textX}" y="${curY - 4}" font-family="${bodyFont}" font-size="12" font-weight="bold" fill="#555555">${escapeXml(tagLine)}</text>`);
          curY += 18;
        }

        if (item.description) {
          const descLines = wordWrap(item.description, 36);
          for (const dline of descLines) {
            elements.push(`<text x="${textX}" y="${curY - 4}" font-family="${bodyFont}" font-size="13" font-style="italic" fill="#666666">${escapeXml(dline)}</text>`);
            curY += 18;
          }
        }
      }

      curY += 8;
      if (borderStyle === "notebook") {
        elements.push(`<line x1="${marginX}" y1="${curY - 2}" x2="${width - marginX}" y2="${curY - 2}" stroke="#d0d8e8" stroke-width="1" />`);
      }
    }
  };

  if (opts.categories && opts.categories.length > 0) {
    for (const cat of opts.categories) {
      curY += 12;
      const catText = cat.name.toUpperCase();
      const badgeWidth = Math.min(contentWidth, catText.length * 10 + 28);
      elements.push(`<rect x="${marginX}" y="${curY - 14}" width="${badgeWidth}" height="24" fill="#000000" rx="12" />`);
      elements.push(`<text x="${marginX + badgeWidth / 2}" y="${curY + 2}" font-family="${displayFont}" font-size="12" font-weight="bold" fill="#ffffff" text-anchor="middle" letter-spacing="1.5">${escapeXml(catText)}</text>`);
      curY += 24;

      renderTaskList(cat.items);
      curY += 10;
    }
  } else if (opts.items && opts.items.length > 0) {
    renderTaskList(opts.items);
  }

  if (opts.recipe) {
    const r = opts.recipe;
    const metaPills: string[] = [];
    if (r.prepTime) metaPills.push(`Prep: ${r.prepTime}`);
    if (r.cookTime) metaPills.push(`Cook: ${r.cookTime}`);
    if (r.servings) metaPills.push(`Yield: ${r.servings}`);

    if (metaPills.length > 0) {
      elements.push(`<rect x="${marginX}" y="${curY}" width="${contentWidth}" height="28" fill="#f0f0f0" stroke="#cccccc" stroke-width="1" rx="6" />`);
      elements.push(`<text x="${width / 2}" y="${curY + 18}" font-family="${bodyFont}" font-size="13" font-weight="bold" fill="#222222" text-anchor="middle">${escapeXml(metaPills.join("   •   "))}</text>`);
      curY += 40;
    }

    if (r.ingredients && r.ingredients.length > 0) {
      elements.push(`<text x="${marginX}" y="${curY}" font-family="${displayFont}" font-size="18" font-weight="bold" fill="#000000" letter-spacing="1">INGREDIENTS</text>`);
      elements.push(`<line x1="${marginX}" y1="${curY + 6}" x2="${width - marginX}" y2="${curY + 6}" stroke="#000000" stroke-width="1.5" />`);
      curY += 24;

      for (const ing of r.ingredients) {
        elements.push(`<circle cx="${marginX + 8}" cy="${curY - 5}" r="3" fill="#000000" />`);
        const ingLines = wordWrap(ing, 34);
        for (const ingLine of ingLines) {
          elements.push(`<text x="${marginX + 22}" y="${curY}" font-family="${bodyFont}" font-size="15" font-weight="500" fill="#111111">${escapeXml(ingLine)}</text>`);
          curY += 22;
        }
        curY += 2;
      }
      curY += 16;
    }

    if (r.instructions && r.instructions.length > 0) {
      elements.push(`<text x="${marginX}" y="${curY}" font-family="${displayFont}" font-size="18" font-weight="bold" fill="#000000" letter-spacing="1">DIRECTIONS</text>`);
      elements.push(`<line x1="${marginX}" y1="${curY + 6}" x2="${width - marginX}" y2="${curY + 6}" stroke="#000000" stroke-width="1.5" />`);
      curY += 24;

      for (let i = 0; i < r.instructions.length; i++) {
        const stepNum = i + 1;
        elements.push(`<circle cx="${marginX + 12}" cy="${curY - 4}" r="11" fill="#000000" />`);
        elements.push(`<text x="${marginX + 12}" y="${curY}" font-family="${bodyFont}" font-size="12" font-weight="bold" fill="#ffffff" text-anchor="middle">${stepNum}</text>`);

        const stepLines = wordWrap(r.instructions[i], 32);
        let stepY = curY;
        for (const sline of stepLines) {
          elements.push(`<text x="${marginX + 32}" y="${stepY}" font-family="${bodyFont}" font-size="15" fill="#111111">${escapeXml(sline)}</text>`);
          stepY += 22;
        }
        curY = stepY + 8;
      }
    }
  }

  curY += 16;
  if (theme === "framed_food" || theme === "bold") {
    elements.push(`<line x1="${marginX}" y1="${curY}" x2="${width - marginX}" y2="${curY}" stroke="#000000" stroke-width="2" />`);
    curY += 16;
    elements.push(`<text x="${width / 2}" y="${curY}" font-family="${bodyFont}" font-size="11" font-weight="bold" fill="#777777" text-anchor="middle" letter-spacing="4">★ THERMALIST PRINT ★</text>`);
    curY += 24;
  } else if (theme === "reminders_notebook") {
    elements.push(`<line x1="${marginX}" y1="${curY}" x2="${width - marginX}" y2="${curY}" stroke="#d0d8e8" stroke-width="1" />`);
    curY += 24;
  } else {
    elements.push(`<line x1="${marginX}" y1="${curY}" x2="${width - marginX}" y2="${curY}" stroke="#000000" stroke-width="1" stroke-dasharray="4,4" />`);
    curY += 20;
  }

  const totalHeight = Math.max(280, curY + 24);
  const frameElements: string[] = [];
  if (borderStyle === "double") {
    frameElements.push(`<rect x="8" y="8" width="${width - 16}" height="${totalHeight - 16}" fill="none" stroke="#000000" stroke-width="4" rx="4" />`);
    frameElements.push(`<rect x="15" y="15" width="${width - 30}" height="${totalHeight - 30}" fill="none" stroke="#000000" stroke-width="1.5" rx="2" />`);
  } else if (borderStyle === "thick") {
    frameElements.push(`<rect x="10" y="10" width="${width - 20}" height="${totalHeight - 20}" fill="none" stroke="#000000" stroke-width="8" />`);
  } else if (borderStyle === "round") {
    frameElements.push(`<rect x="10" y="10" width="${width - 20}" height="${totalHeight - 20}" fill="none" stroke="#000000" stroke-width="3.5" rx="24" />`);
  } else if (borderStyle === "notebook") {
    frameElements.push(`<line x1="36" y1="8" x2="36" y2="${totalHeight - 8}" stroke="#ff6b6b" stroke-width="2" />`);
    frameElements.push(`<line x1="8" y1="8" x2="${width - 8}" y2="8" stroke="#333333" stroke-width="2" />`);
    frameElements.push(`<line x1="8" y1="${totalHeight - 8}" x2="${width - 8}" y2="${totalHeight - 8}" stroke="#333333" stroke-width="2" />`);
  }

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${totalHeight}" viewBox="0 0 ${width} ${totalHeight}">
  <defs><style>text { text-rendering: geometricPrecision; }</style></defs>
  <rect width="${width}" height="${totalHeight}" fill="#ffffff" />
  ${frameElements.join("\n  ")}
  ${elements.join("\n  ")}
</svg>`;

  return { svg, width, height: totalHeight };
}

export function saveGraphicOutput(filename: string, svg: string): string {
  const generatedImagesDir = path.join(process.cwd(), "generated_images");
  if (!fs.existsSync(generatedImagesDir)) {
    fs.mkdirSync(generatedImagesDir, { recursive: true });
  }
  const filePath = path.join(generatedImagesDir, filename);
  fs.writeFileSync(filePath, svg, "utf-8");
  return `/generated_images/${filename}?t=${Date.now()}`;
}
