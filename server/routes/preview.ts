import { Router, Request, Response } from "express";
import { DocumentModel, DocumentSection, Receipt80mmRenderer, TaskItem } from "../renderers/receipt.js";
import { renderAndSaveLabel } from "../renderers/label.js";
import { config } from "../config.js";

export const previewRouter = Router();

// Sample DoneTick tasks for offline / preview fallback
export const SAMPLE_DONETICK_TASKS: TaskItem[] = [
  {
    id: "1",
    title: "Change HVAC air filter",
    completed: false,
    labels: ["House Maintenance"],
    due: "Tomorrow",
    description: "Use 20x25x1 MERV 11 filter in hallway intake",
  },
  {
    id: "2",
    title: "Clean kitchen disposal with citrus peel",
    completed: false,
    labels: ["House Maintenance"],
    due: "Friday",
    description: "Run cold water while grinding lemon peels",
  },
  {
    id: "3",
    title: "Restock pantry staple spices",
    completed: false,
    labels: ["Shopping"],
    due: null,
    description: "Cumin, smoked paprika, kosher salt",
  },
  {
    id: "4",
    title: "Pick up dry cleaning",
    completed: false,
    labels: ["Errands"],
    due: "Today",
    description: "Ticket #4182 on Broadway",
  },
  {
    id: "5",
    title: "Water indoor houseplants",
    completed: true,
    labels: ["Personal"],
    due: null,
    description: "Monstera and fiddle leaf fig",
  },
];

export async function fetchDoneTickTasks(options: Record<string, any> = {}): Promise<TaskItem[]> {
  const baseUrl = config.donetick.base_url;
  const token = config.donetick.token;

  if (baseUrl && token) {
    try {
      const resp = await fetch(`${baseUrl.replace(/\/$/, "")}/api/tasks`, {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/json",
        },
        signal: AbortSignal.timeout(3000),
      });
      if (resp.ok) {
        const data = (await resp.json()) as any;
        const rawTasks = Array.isArray(data) ? data : data.tasks || [];
        if (rawTasks.length > 0) {
          return rawTasks.map((t: any, idx: number) => ({
            id: String(t.id || idx + 1),
            title: t.title || t.name || "Untitled Task",
            completed: !!t.completed,
            labels: Array.isArray(t.labels) ? t.labels : t.label ? [t.label] : [],
            due: t.due ? String(t.due) : null,
            description: t.description || "",
            subtasks: Array.isArray(t.subtasks) ? t.subtasks : [],
          }));
        }
      }
    } catch (err: any) {
      console.warn(`[DoneTick] Live fetch failed, using fallback: ${err?.message}`);
    }
  }

  return SAMPLE_DONETICK_TASKS;
}

export function buildDocumentFromRequest(
  moduleName: string,
  content: any,
  tasks: TaskItem[],
  renderOptions: Record<string, any> = {}
): DocumentModel {
  if (moduleName === "notes") {
    const title = (content?.title || "Note").trim();
    const body = (content?.body || "").trim();
    return {
      title,
      sections: [
        { kind: "title", text: title },
        { kind: "text", text: body },
      ],
      metadata: { module: "notes" },
    };
  }

  if (moduleName === "todo") {
    const title = (content?.title || "Todo List").trim();
    const showLabels = renderOptions.show_labels !== false;
    const showCompleted = renderOptions.show_completed !== false;

    const filteredTasks = tasks.filter((t) => (showCompleted ? true : !t.completed));

    const grouped = new Map<string, TaskItem[]>();
    for (const t of filteredTasks) {
      const labelName = t.labels && t.labels.length > 0 ? t.labels[0] : "General";
      if (!grouped.has(labelName)) grouped.set(labelName, []);
      grouped.get(labelName)!.push(t);
    }

    const sections: DocumentSection[] = [{ kind: "title", text: title }];

    for (const [groupName, groupTasks] of grouped.entries()) {
      if (showLabels && grouped.size > 1) {
        sections.push({ kind: "text", text: `-- ${groupName} --` });
      }
      sections.push({ kind: "task_list", tasks: groupTasks });
    }

    return {
      title,
      sections,
      metadata: { module: "todo" },
    };
  }

  if (moduleName === "recipe") {
    const recipe = content?.recipe || {};
    const title = (recipe.title || recipe.name || "Recipe").trim();

    const sections: DocumentSection[] = [{ kind: "title", text: title }];

    const timeParts: string[] = [];
    if (recipe.servings) timeParts.push(`Serves ${recipe.servings}`);
    if (recipe.prep_time) timeParts.push(`Prep: ${recipe.prep_time}`);
    if (recipe.cook_time) timeParts.push(`Cook: ${recipe.cook_time}`);
    if (recipe.total_time) timeParts.push(`Total: ${recipe.total_time}`);

    if (timeParts.length > 0) {
      sections.push({ kind: "text", text: timeParts.join(" | ") });
    }

    if (recipe.description) {
      sections.push({ kind: "text", text: String(recipe.description).trim() });
    }

    const ingredients = Array.isArray(recipe.ingredients)
      ? recipe.ingredients.map((ing: any) =>
          typeof ing === "string" ? { text: ing } : { text: ing.text || ing.original_text || String(ing) }
        )
      : [];

    if (ingredients.length > 0) {
      sections.push({ kind: "divider" });
      sections.push({ kind: "text", text: "INGREDIENTS" });
      sections.push({ kind: "ingredient_list", ingredients });
    }

    const steps = Array.isArray(recipe.steps || recipe.instructions)
      ? (recipe.steps || recipe.instructions).map((st: any, idx: number) => ({
          number: st.number || idx + 1,
          text: typeof st === "string" ? st : st.text || st.instruction || String(st),
        }))
      : [];

    if (steps.length > 0) {
      sections.push({ kind: "divider" });
      sections.push({ kind: "text", text: "STEPS" });
      sections.push({ kind: "step_list", steps });
    }

    if (recipe.source_url) {
      sections.push({ kind: "divider" });
      sections.push({ kind: "text", text: recipe.source_url });
    }

    return {
      title,
      sections,
      metadata: { module: "recipe" },
    };
  }

  // Label module text fallback
  return {
    title: "Label",
    sections: [
      {
        kind: "label",
        text: content?.verb || "Opened",
        metadata: { date: content?.date, note: content?.note },
      },
    ],
    metadata: { module: "label" },
  };
}

previewRouter.post("", async (req: Request, res: Response) => {
  const body = req.body || {};
  const moduleName = body.module_name || "notes";
  const renderConfig = body.render_config || {};
  const renderOptions = {
    ...(body.render_options || {}),
    ...(body.module_options || {}),
  };

  const font = renderConfig.font || "A";
  const width = Number(renderConfig.width) || (font === "A" ? 48 : 56);

  // If label bitmap is requested via preview:
  if (moduleName === "label" && (renderOptions.mode === "bitmap" || renderConfig.renderer === "label_bitmap")) {
    const result = renderAndSaveLabel(
      {
        verb: body.content?.verb || "Opened",
        date: body.content?.date || "",
        note: body.content?.note || "",
        subtext: body.content?.subtext,
      },
      body.theme_name || "framed_food"
    );
    return res.json({
      ...result,
      module: "label",
      mode: "bitmap",
    });
  }

  let tasks: TaskItem[] = [];
  let resolvedSource: string | null = null;

  if (moduleName === "todo") {
    if (body.source_name === "donetick") {
      resolvedSource = "donetick";
      const allTasks = await fetchDoneTickTasks(body.source_options || {});
      const labelFilter = body.source_options?.label_filter?.trim();
      if (labelFilter) {
        tasks = allTasks.filter((t) => t.labels?.some((l) => l.toLowerCase() === labelFilter.toLowerCase()));
      } else {
        tasks = allTasks;
      }
    } else {
      tasks = (body.content?.items || []).map((t: any, idx: number) => ({
        id: String(idx + 1),
        title: t.title || "Task",
        completed: !!t.completed,
        labels: Array.isArray(t.labels) ? t.labels : [],
        due: t.due || null,
        description: t.description || "",
      }));
    }
  }

  const document = buildDocumentFromRequest(moduleName, body.content, tasks, renderOptions);
  const renderer = new Receipt80mmRenderer(width, renderOptions.show_due !== false);
  const receipt = renderer.render(document);

  return res.json({
    document,
    receipt,
    source: resolvedSource,
    module: moduleName,
  });
});
