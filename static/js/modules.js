import { state, els, showEditor } from "./state.js";

export function toggleRecipeSourceMode() {
  const mode = els.recipeSourceMode?.value || "url";

  if (els.recipeUrlControls) {
    els.recipeUrlControls.style.display = mode === "url" ? "" : "none";
  }

  if (els.recipeMealieControls) {
    els.recipeMealieControls.style.display = mode === "mealie" ? "" : "none";
  }
}

export function syncDateFilterControls() {
  if (
    !els.doneTickDateFilterSelect ||
    !els.doneTickIncludeOverdueWrap ||
    !els.doneTickIncludeOverdue
  ) {
    return;
  }

  const mode = els.doneTickDateFilterSelect.value;
  const showIncludeOverdue = mode !== "overdue";

  els.doneTickIncludeOverdueWrap.style.display = showIncludeOverdue ? "" : "none";

  if (!showIncludeOverdue) {
    els.doneTickIncludeOverdue.checked = false;
  }
}

export async function toggleTodoSourceMode() {
  const useDoneTick =
    els.moduleSelect?.value === "todo" && els.todoSourceMode?.value === "donetick";

  if (els.doneTickControls) {
    els.doneTickControls.style.display = useDoneTick ? "" : "none";
  }

  if (els.manualTodoControls) {
    els.manualTodoControls.style.display = useDoneTick ? "none" : "";
  }

  if (
    useDoneTick &&
    !state.doneTickLabelsLoaded &&
    els.loadLabelsBtn &&
    els.doneTickLabelSelect
  ) {
    state.doneTickLabelsLoaded = await loadDoneTickLabels();
  }
}

export function toggleForms() {
  const mod = els.moduleSelect?.value || "notes";

  if (els.notesForm) els.notesForm.style.display = mod === "notes" ? "" : "none";
  if (els.todoForm) els.todoForm.style.display = mod === "todo" ? "" : "none";
  if (els.labelForm) els.labelForm.style.display = mod === "label" ? "" : "none";
  if (els.recipeForm) els.recipeForm.style.display = mod === "recipe" ? "" : "none";

  if (els.optionsSection) {
    els.optionsSection.hidden = mod !== "todo" && mod !== "recipe";
  }

  toggleTodoSourceMode();

  if (mod === "recipe") {
    toggleRecipeSourceMode();
  }
}

export function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export function createTodoItem(task = {}) {
  const wrapper = document.createElement("div");
  wrapper.className = "todo-item";

  wrapper.innerHTML = `
    <div class="todo-item-top">
      <div class="todo-item-title">Task</div>
      <button type="button" class="todo-remove">Remove</button>
    </div>

    <label>
      Title
      <input type="text" class="todo-task-title" value="${escapeHtml(task.title || "")}" placeholder="Task title">
    </label>

    <label>
      Labels
      <input type="text" class="todo-task-labels" value="${escapeHtml((task.labels || []).join(", "))}" placeholder="House Maintenance, Errands">
    </label>

    <label>
      Description
      <textarea class="todo-task-description" placeholder="Optional description">${escapeHtml(task.description || "")}</textarea>
    </label>

    <label class="todo-check">
      <input type="checkbox" class="todo-task-completed" ${task.completed ? "checked" : ""}>
      Completed
    </label>
  `;

  return wrapper;
}

export function addTodoItem(task = {}) {
  if (!els.todoItemsContainer) return;
  els.todoItemsContainer.appendChild(createTodoItem(task));
}

export function getTodoItems() {
  if (!els.todoItemsContainer) return [];

  return Array.from(els.todoItemsContainer.querySelectorAll(".todo-item"))
    .map((item, index) => {
      const title = item.querySelector(".todo-task-title")?.value.trim() || "";
      const labelsRaw = item.querySelector(".todo-task-labels")?.value.trim() || "";
      const description =
        item.querySelector(".todo-task-description")?.value.trim() || "";
      const completed =
        item.querySelector(".todo-task-completed")?.checked || false;

      const labels = labelsRaw
        ? labelsRaw
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean)
        : [];

      return {
        id: String(index + 1),
        title,
        completed,
        labels,
        due: null,
        description,
        metadata: {},
      };
    })
    .filter((task) => task.title);
}

export function syncPreviewTextWidth() {
  if (!els.widthInput || !els.fontSelect) return;

  const width =
    Number(els.widthInput.value) || (els.fontSelect.value === "A" ? 48 : 56);

  document.documentElement.style.setProperty("--receipt-columns", width);
}

export function updateWidthFromFont() {
  if (!els.widthInput || !els.fontSelect) return;

  const current = Number(els.widthInput.value);
  if (!current || current === 48 || current === 56) {
    els.widthInput.value = els.fontSelect.value === "A" ? 48 : 56;
  }
}

export function setActiveVerbChip(activeVerb) {
  document.querySelectorAll(".verb-chip").forEach((chip) => {
    const isActive = chip.dataset.verb === activeVerb;
    chip.classList.toggle("is-active", isActive);
    chip.setAttribute("aria-pressed", String(isActive));
  });
}

export function syncLabelVerbChipState() {
  const currentVerb = els.labelVerb?.value.trim() || "";
  setActiveVerbChip(currentVerb);
}

export function initLabelDate() {
  if (!els.labelDate || els.labelDate.value) return;

  const today = new Date();
  const yyyy = today.getFullYear();
  const mm = String(today.getMonth() + 1).padStart(2, "0");
  const dd = String(today.getDate()).padStart(2, "0");
  els.labelDate.value = `${yyyy}-${mm}-${dd}`;
}

export function buildRequest() {
  const moduleName = els.moduleSelect?.value || "notes";
  const font = els.fontSelect?.value || "A";
  const width = Number(els.widthInput?.value) || (font === "A" ? 48 : 56);

  const req = {
    module_name: moduleName,
    output_kind: "raw_tcp",
    render_config: { font, width },
    output_config: { dry_run: false },
    render_options: { ...state.renderOptions },
  };

  if (moduleName === "notes") {
    req.content = {
      title: document.getElementById("title")?.value || "",
      body: document.getElementById("body")?.value || "",
    };
  } else if (moduleName === "recipe") {
    req.module_options = {
      variant: "cook-card",
      include_description: true,
      include_times: true,
      include_labels: false,
      include_source_url: true,
    };

    req.content = state.importedRecipe
      ? { recipe: state.importedRecipe }
      : { recipe: null };
  } else if (moduleName === "todo") {
    if (els.todoSourceMode?.value === "donetick") {
      req.source_name = "donetick";
      req.source_options = {};

      const labelFilter = els.doneTickLabelSelect?.value.trim() || "";
      if (labelFilter) {
        req.source_options.label_filter = labelFilter;
      }

      const dateFilter = els.doneTickDateFilterSelect?.value || "";
      if (dateFilter) {
        req.source_options.date_filter = dateFilter;
      }

      req.source_options.include_overdue = !!els.doneTickIncludeOverdue?.checked;
    } else {
      req.content = {
        title: document.getElementById("todoTitle")?.value.trim() || "Todo List",
        items: getTodoItems(),
      };
    }
  } else if (moduleName === "label") {
    if (els.labelDate && !els.labelDate.value) {
      els.labelDate.value = new Date().toISOString().slice(0, 10);
    }

    const raw = els.labelDate?.value || "";
    let formatted = "";

    if (raw) {
      const [yyyy, mm, dd] = raw.split("-");
      formatted = `${mm}/${dd}/${String(yyyy).slice(2)}`;
    }

    req.content = {
      verb: els.labelVerb?.value.trim() || "Opened",
      date: formatted,
      note: els.labelNote?.value.trim() || "",
    };
    req.theme_name = els.labelTheme?.value || "framed_food";
  }

  return req;
}

export async function loadMealieRecipes() {
  if (!els.loadMealieRecipesBtn || !els.mealieRecipeSelect) return false;

  els.loadMealieRecipesBtn.disabled = true;
  els.mealieRecipeSelect.disabled = true;
  els.mealieRecipeSelect.innerHTML = "";
  els.mealieRecipeSelect.appendChild(new Option("Loading recipes…", ""));

  try {
    const search = els.mealieRecipeSearch?.value.trim() || "";
    const url = new URL("/recipes/mealie", window.location.origin);
    if (search) {
      url.searchParams.set("search", search);
    }

    const res = await fetch(url.toString());
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status}: ${text}`);
    }

    const data = await res.json();
    const recipes = Array.isArray(data.recipes) ? data.recipes : [];

    els.mealieRecipeSelect.innerHTML = "";
    els.mealieRecipeSelect.appendChild(new Option("Select a recipe", ""));

    recipes.forEach((recipe) => {
      const value = recipe.slug || recipe.id || "";
      const label = recipe.name || recipe.title || value;
      els.mealieRecipeSelect.appendChild(new Option(label, value));
    });

    els.mealieRecipeSelect.disabled = false;
    state.mealieRecipesLoaded = true;
    return true;
  } catch (err) {
    els.mealieRecipeSelect.innerHTML = "";
    els.mealieRecipeSelect.appendChild(new Option("Failed to load recipes", ""));
    els.mealieRecipeSelect.disabled = true;
    state.mealieRecipesLoaded = false;
    return false;
  } finally {
    els.loadMealieRecipesBtn.disabled = false;
  }
}

export async function importRecipeFromUrl() {
  const url = els.recipeSourceUrl?.value.trim();
  if (!url) return;

  const resp = await fetch("/recipes/import", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

  if (!resp.ok) {
    console.error("Import failed", await resp.json());
    return;
  }

  const data = await resp.json();
  state.importedRecipe = data.recipe;
}

export async function importRecipeFromMealie() {
  const slug = els.mealieRecipeSelect?.value.trim();
  if (!slug) return;

  const res = await fetch(`/recipes/mealie/${encodeURIComponent(slug)}`);
  if (!res.ok) {
    console.error("Mealie recipe fetch failed", await res.json());
    return;
  }

  const data = await res.json();
  state.importedRecipe = data.recipe;
}

export async function loadLabelThemes() {
  if (!els.labelTheme) return;

  els.labelTheme.disabled = true;
  els.labelTheme.innerHTML = '<option value="">Loading themes…</option>';

  try {
    const res = await fetch("/api/labels/themes");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();
    const themes = Array.isArray(data) ? data : [];

    els.labelTheme.innerHTML = "";
    themes.forEach((theme) => {
      const opt = document.createElement("option");
      opt.value = theme.value;
      opt.textContent = theme.label;
      els.labelTheme.appendChild(opt);
    });

    const defaultTheme = "framed_food";
    if ([...els.labelTheme.options].some((o) => o.value === defaultTheme)) {
      els.labelTheme.value = defaultTheme;
    } else {
      els.labelTheme.value = els.labelTheme.options[0]?.value || "";
    }
  } catch (err) {
    console.error("Failed to load label themes", err);
    els.labelTheme.innerHTML =
      '<option value="framed_food">Framed Food (default)</option>';
    els.labelTheme.value = "framed_food";
  } finally {
    els.labelTheme.disabled = false;
  }
}

export async function loadDoneTickLabels() {
  if (!els.loadLabelsBtn || !els.doneTickLabelSelect) return false;

  els.loadLabelsBtn.disabled = true;
  els.doneTickLabelSelect.disabled = true;
  els.doneTickLabelSelect.innerHTML = "";
  els.doneTickLabelSelect.appendChild(new Option("Loading labels…", ""));

  try {
    const res = await fetch("/sources/donetick/labels");
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status}: ${text}`);
    }

    const data = await res.json();
    const labels = Array.isArray(data.labels) ? data.labels : [];

    els.doneTickLabelSelect.innerHTML = "";
    els.doneTickLabelSelect.appendChild(new Option("All labels", ""));
    labels.forEach((label) => {
      els.doneTickLabelSelect.appendChild(new Option(label, label));
    });

    els.doneTickLabelSelect.disabled = false;
    return true;
  } catch (err) {
    els.doneTickLabelSelect.innerHTML = "";
    els.doneTickLabelSelect.appendChild(new Option("Failed to load labels", ""));
    els.doneTickLabelSelect.disabled = true;
    return false;
  } finally {
    els.loadLabelsBtn.disabled = false;
  }
}

export function openModule(moduleName, options = {}) {
  if (els.moduleSelect) {
    els.moduleSelect.value = moduleName;
  }

  if (moduleName === "todo" && els.todoSourceMode) {
    els.todoSourceMode.value = options.todoSourceMode || "manual";
  }

  toggleForms();
  showEditor();

  if (moduleName === "todo" && options.todoSourceMode === "donetick") {
    loadDoneTickLabels();
  }
}