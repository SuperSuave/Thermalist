export interface RenderOptions {
  show_labels?: boolean;
  show_due?: boolean;
  show_description?: boolean;
  show_subtasks?: boolean;
  variant?: string;
  include_description?: boolean;
  include_times?: boolean;
  include_labels?: boolean;
  include_source_url?: boolean;
  max_steps?: number;
  max_ingredients?: number;
}

export interface TaskItem {
  id?: string;
  title: string;
  completed?: boolean;
  labels?: string[];
  due?: string | null;
  description?: string;
  subtasks?: TaskItem[];
}

export interface IngredientItem {
  text?: string;
  original_text?: string;
}

export interface StepItem {
  number: number;
  text: string;
}

export interface DocumentSection {
  kind: "title" | "text" | "divider" | "spacer" | "label" | "task_list" | "ingredient_list" | "step_list";
  text?: string;
  metadata?: Record<string, any>;
  tasks?: TaskItem[];
  ingredients?: IngredientItem[];
  steps?: StepItem[];
}

export interface DocumentModel {
  title: string;
  sections: DocumentSection[];
  metadata?: Record<string, any>;
}

export interface RenderedReceipt {
  text_preview: string;
  raw_bytes?: string | null;
  metadata: {
    renderer: string;
    width: number;
  };
}

function stripUnsupportedChars(text: string): string {
  if (!text) return "";
  return text
    .split("\n")
    .map((line) => line.trim())
    .join("\n");
}

function wrapWords(text: string, width: number): string[] {
  if (!text) return [];
  const words = text.split(/\s+/).filter(Boolean);
  if (!words.length) return [];

  const lines: string[] = [];
  let current = "";

  for (const word of words) {
    if (!current) {
      current = word;
    } else if (current.length + 1 + word.length <= width) {
      current += " " + word;
    } else {
      lines.push(current);
      current = word;
    }
  }
  if (current) lines.push(current);
  return lines;
}

export class Receipt80mmRenderer {
  name = "receipt_80mm";
  width: number;
  show_due: boolean;

  constructor(width = 48, show_due = true) {
    this.width = width;
    this.show_due = show_due;
  }

  center(text: string): string {
    const trimmed = text.slice(0, this.width);
    const leftPad = Math.max(0, Math.floor((this.width - trimmed.length) / 2));
    const rightPad = Math.max(0, this.width - trimmed.length - leftPad);
    return " ".repeat(leftPad) + trimmed + " ".repeat(rightPad);
  }

  divider(char = "-"): string {
    const repeated = char.repeat(Math.ceil(this.width / char.length) + 1);
    return repeated.slice(0, this.width);
  }

  boxLine(text: string, inner: number): string {
    const trimmed = text.slice(0, inner);
    const leftPad = Math.max(0, Math.floor((inner - trimmed.length) / 2));
    const rightPad = Math.max(0, inner - trimmed.length - leftPad);
    return "|" + " ".repeat(leftPad) + trimmed + " ".repeat(rightPad) + "|";
  }

  wrapIndented(prefix: string, text: string, indent = "    "): string[] {
    if (!text) return prefix.trimEnd() ? [prefix.trimEnd()] : [];
    const availFirst = Math.max(8, this.width - prefix.length);
    const words = text.split(/\s+/).filter(Boolean);
    if (!words.length) return [prefix.trimEnd()];

    const lines: string[] = [];
    let current = "";

    for (let i = 0; i < words.length; i++) {
      const w = words[i];
      const maxLen = lines.length === 0 ? availFirst : this.width - indent.length;

      if (!current) {
        current = w;
      } else if (current.length + 1 + w.length <= maxLen) {
        current += " " + w;
      } else {
        if (lines.length === 0) {
          lines.push(prefix + current);
        } else {
          lines.push(indent + current);
        }
        current = w;
      }
    }

    if (current) {
      if (lines.length === 0) {
        lines.push(prefix + current);
      } else {
        lines.push(indent + current);
      }
    }

    return lines;
  }

  wrap(text: string, indent = ""): string[] {
    if (!text) return [];
    const lines: string[] = [];
    const paragraphs = text.split("\n");

    for (const p of paragraphs) {
      if (!p.trim()) {
        lines.push("");
      } else {
        const wrapped = wrapWords(p, this.width - indent.length);
        for (const line of wrapped) {
          lines.push(indent + line);
        }
      }
    }
    return lines;
  }

  render(document: DocumentModel): RenderedReceipt {
    const lines: string[] = [];

    for (const section of document.sections) {
      if (section.kind === "title" && section.text) {
        const title = stripUnsupportedChars(section.text.trim().toUpperCase());
        const today = new Date().toLocaleDateString("en-US", {
          month: "2-digit",
          day: "2-digit",
          year: "2-digit",
        });
        lines.push(this.center(title));
        lines.push(this.center(today));
        lines.push(this.divider("^v"));
        lines.push("");
      } else if (section.kind === "text" && section.text) {
        lines.push(...this.wrap(stripUnsupportedChars(section.text)));
      } else if (section.kind === "divider") {
        lines.push(this.divider("-"));
      } else if (section.kind === "spacer") {
        lines.push("");
      } else if (section.kind === "label") {
        const inner = this.width - 2;
        const border = "+" + "-".repeat(inner) + "+";
        const blank = "|" + " ".repeat(inner) + "|";
        lines.push(border, blank);
        if (section.text) {
          lines.push(this.boxLine(section.text, inner));
        }
        if (section.metadata?.date) {
          lines.push(this.boxLine(section.metadata.date, inner));
        }
        if (section.metadata?.note) {
          lines.push(blank);
          lines.push(this.boxLine(section.metadata.note, inner));
        }
        lines.push(blank, border);
      } else if (section.kind === "task_list" && section.tasks) {
        for (const item of section.tasks) {
          const title = stripUnsupportedChars(item.title || "");
          const prefix = item.completed ? "[x] " : "[ ] ";
          lines.push(...this.wrapIndented(prefix, title, "    "));

          if (item.description) {
            lines.push(...this.wrap(stripUnsupportedChars(item.description), "    "));
          }

          if (item.subtasks?.length) {
            for (const sub of item.subtasks) {
              const subTitle = stripUnsupportedChars(sub.title || "");
              const subPrefix = sub.completed ? "    [x] " : "    [ ] ";
              lines.push(...this.wrapIndented(subPrefix, subTitle, "        "));
              if (sub.description) {
                lines.push(...this.wrap(stripUnsupportedChars(sub.description), "        "));
              }
              if (this.show_due && sub.due) {
                lines.push(...this.wrap(stripUnsupportedChars(`Due: ${sub.due}`), "        "));
              }
            }
          }

          if (this.show_due && item.due) {
            lines.push(...this.wrap(stripUnsupportedChars(`Due: ${item.due}`), "    "));
          }
          lines.push("");
        }
      } else if (section.kind === "ingredient_list" && section.ingredients) {
        for (const ing of section.ingredients) {
          const ingText = stripUnsupportedChars(ing.text || ing.original_text || "");
          lines.push(...this.wrapIndented("- ", ingText, "   "));
        }
        lines.push("");
      } else if (section.kind === "step_list" && section.steps) {
        for (const step of section.steps) {
          const stepText = stripUnsupportedChars(step.text || "");
          lines.push(...this.wrapIndented(`${step.number}. `, stepText, "   "));
        }
        lines.push("");
      }
    }

    while (lines.length && lines[lines.length - 1] === "") {
      lines.pop();
    }
    lines.push("", "");

    return {
      text_preview: lines.join("\n"),
      metadata: {
        renderer: this.name,
        width: this.width,
      },
    };
  }
}
