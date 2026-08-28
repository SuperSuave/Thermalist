const apiBase = "";
let abortController = null;
let doneTickLabelsLoaded = false;
let previewDebounceTimer = null;

const appEl = document.querySelector(".app");
const sidebarEl = document.getElementById("sidebar");
const homeScreenEl = document.getElementById("homeScreen");
const previewPanelEl = document.getElementById("previewPanel");
const homeBtnEl = document.getElementById("homeBtn");
const receiptPaper = document.querySelector(".receipt-paper");
const printButton = document.getElementById("printBtn");

const moduleSelect = document.getElementById("module");
const notesForm = document.getElementById("notesForm");
const previewEl = document.getElementById("preview");
const statusEl = document.getElementById("status");
const fontSelect = document.getElementById("font");
const widthInput = document.getElementById("width");

const manualTodoControls = document.getElementById("manualTodoControls");
const optionsSection = document.getElementById("optionsSection");
const todoSourceMode = document.getElementById("todoSourceMode");
const todoItemsContainer = document.getElementById("todoItemsContainer");
const addTaskBtn = document.getElementById("addTaskBtn");
const todoForm = document.getElementById("todoForm");

const doneTickLabelSelect = document.getElementById("doneTickLabelSelect");
const doneTickControls = document.getElementById("doneTickControls");
const doneTickDateFilterSelect = document.getElementById(
  "doneTickDateFilterSelect",
);
const doneTickIncludeOverdueWrap = document.getElementById(
  "doneTickIncludeOverdueWrap",
);
const doneTickIncludeOverdue = document.getElementById(
  "doneTickIncludeOverdue",
);
const loadLabelsBtn = document.getElementById("loadLabelsBtn");

const labelDate = document.getElementById("labelDate");
const labelForm = document.getElementById("labelForm");
const labelNote = document.getElementById("labelNote");
const labelVerb = document.getElementById("labelVerb");
const labelPreviewImage = document.getElementById("labelPreviewImage");
const labelTheme = document.getElementById("labelTheme");

const recipeForm = document.getElementById("recipeForm");
const recipeSourceUrl = document.getElementById("recipeSourceUrl");
const recipeSourceMode = document.getElementById("recipeSourceMode");
const recipeUrlControls = document.getElementById("recipeUrlControls");
const recipeMealieControls = document.getElementById("recipeMealieControls");
const mealieRecipeSearch = document.getElementById("mealieRecipeSearch");
const mealieRecipeSelect = document.getElementById("mealieRecipeSelect");
const loadMealieRecipesBtn = document.getElementById("loadMealieRecipesBtn");

let mealieRecipesLoaded = false;
let importedRecipe = null;
let selectedMealieRecipe = null;

const renderOptions = {
  show_labels: true,
  show_due: true,
  show_description: true,
  show_subtasks: true,
};

function setScreen(mode) {
  const update = () => {
    if (mode === "home") {
      homeScreenEl?.removeAttribute("hidden");
      sidebarEl?.removeAttribute("hidden");
      previewPanelEl?.removeAttribute("hidden");

      homeScreenEl?.setAttribute("aria-hidden", "false");
      sidebarEl?.setAttribute("aria-hidden", "true");
      previewPanelEl?.setAttribute("aria-hidden", "true");

      appEl?.classList.add("is-home");
      appEl?.classList.remove("is-editor");
    } else {
      homeScreenEl?.removeAttribute("hidden");
      sidebarEl?.removeAttribute("hidden");
      previewPanelEl?.removeAttribute("hidden");

      homeScreenEl?.setAttribute("aria-hidden", "true");
      sidebarEl?.setAttribute("aria-hidden", "false");
      previewPanelEl?.setAttribute("aria-hidden", "false");

      appEl?.classList.remove("is-home");
      appEl?.classList.add("is-editor");
    }
  };

  const finalize = () => {
    if (mode === "home") {
      sidebarEl?.setAttribute("hidden", "");
      previewPanelEl?.setAttribute("hidden", "");
      homeScreenEl?.removeAttribute("hidden");
    } else {
      homeScreenEl?.setAttribute("hidden", "");
      sidebarEl?.removeAttribute("hidden");
      previewPanelEl?.removeAttribute("hidden");
    }
  };

  if (!document.startViewTransition) {
    update();
    window.setTimeout(finalize, 500);
    return;
  }

  const transition = document.startViewTransition(() => {
    update();
  });

  transition.updateCallbackDone.finally(() => {
    window.setTimeout(finalize, 500);
  });
}

function showHomeScreen() {
  setScreen("home");
}

function showEditor() {
  setScreen("editor");
}

function debouncePreview(delay = 750) {
  window.clearTimeout(previewDebounceTimer);
  previewDebounceTimer = window.setTimeout(() => {
    requestPreview({ silent: true });
  }, delay);
}

function setDisabledById(id, isLoading) {
  const el = document.getElementById(id);
  if (el) el.disabled = isLoading;
}

function setLoading(isLoading) {
  setDisabledById("refreshBtn", isLoading);
  setDisabledById("printBtn", isLoading);
  setDisabledById("clearBtn", isLoading);

  if (moduleSelect) moduleSelect.disabled = isLoading;
  if (recipeSourceUrl) recipeSourceUrl.disabled = isLoading;

  setDisabledById("title", isLoading);
  setDisabledById("body", isLoading);
  setDisabledById("todoTitle", isLoading);

  if (addTaskBtn) addTaskBtn.disabled = isLoading;
  if (todoSourceMode) todoSourceMode.disabled = isLoading;
  if (loadLabelsBtn) loadLabelsBtn.disabled = isLoading;
  if (doneTickLabelSelect) doneTickLabelSelect.disabled = isLoading;
  if (doneTickDateFilterSelect) doneTickDateFilterSelect.disabled = isLoading;
  if (doneTickIncludeOverdue) doneTickIncludeOverdue.disabled = isLoading;

  todoItemsContainer
    ?.querySelectorAll("input, textarea, button")
    .forEach((el) => {
      el.disabled = isLoading;
    });

  if (fontSelect) fontSelect.disabled = isLoading;
  if (widthInput) widthInput.disabled = isLoading;

  if (labelVerb) labelVerb.disabled = isLoading;
  if (labelDate) labelDate.disabled = isLoading;
  if (labelNote) labelNote.disabled = isLoading;
  if (labelTheme) labelTheme.disabled = isLoading;

  document.querySelectorAll(".verb-chip").forEach((chip) => {
    chip.disabled = isLoading;
  });

  labelForm?.classList.toggle("is-loading", isLoading);
}

function formatApiError(payload, status) {
  if (!payload) return `HTTP ${status}`;

  if (typeof payload.detail === "string") {
    return payload.detail;
  }

  if (Array.isArray(payload.detail)) {
    const first = payload.detail[0];
    if (first?.loc && first?.msg) {
      return `${first.loc.join(".")}: ${first.msg}`;
    }
    return `Request failed with ${payload.detail.length} validation error(s).`;
  }

  if (payload.error) {
    return payload.error;
  }

  return `HTTP ${status}`;
}

function syncDateFilterControls() {
  if (
    !doneTickDateFilterSelect ||
    !doneTickIncludeOverdueWrap ||
    !doneTickIncludeOverdue
  )
    return;

  const mode = doneTickDateFilterSelect.value;
  const showIncludeOverdue = mode !== "overdue";

  doneTickIncludeOverdueWrap.style.display = showIncludeOverdue ? "" : "none";

  if (!showIncludeOverdue) {
    doneTickIncludeOverdue.checked = false;
  }
}

async function toggleTodoSourceMode() {
  const useDoneTick =
    moduleSelect?.value === "todo" && todoSourceMode?.value === "donetick";

  if (doneTickControls)
    doneTickControls.style.display = useDoneTick ? "" : "none";
  if (manualTodoControls)
    manualTodoControls.style.display = useDoneTick ? "none" : "";

  if (
    useDoneTick &&
    !doneTickLabelsLoaded &&
    loadLabelsBtn &&
    doneTickLabelSelect
  ) {
    doneTickLabelsLoaded = await loadDoneTickLabels();
  }
}

function toggleForms() {
  const mod = moduleSelect?.value || "notes";

  if (notesForm) notesForm.style.display = mod === "notes" ? "" : "none";
  if (todoForm) todoForm.style.display = mod === "todo" ? "" : "none";
  if (labelForm) labelForm.style.display = mod === "label" ? "" : "none";
  if (recipeForm) recipeForm.style.display = mod === "recipe" ? "" : "none";

  if (optionsSection) {
    optionsSection.hidden = mod !== "todo" && mod !== "recipe";
  }

  toggleTodoSourceMode();

  if (mod === "recipe") {
    toggleRecipeSourceMode();
  }
}

function openModule(moduleName, options = {}) {
  if (moduleSelect) {
    moduleSelect.value = moduleName;
  }

  if (moduleName === "todo" && todoSourceMode) {
    todoSourceMode.value = options.todoSourceMode || "manual";
  }

  toggleForms();
  setScreen("editor");

  if (moduleName === "todo" && options.todoSourceMode === "donetick") {
    loadDoneTickLabels();
  }

  requestPreview({ silent: true });
}

function toggleRecipeSourceMode() {
  const mode = recipeSourceMode?.value || "url";

  if (recipeUrlControls) {
    recipeUrlControls.style.display = mode === "url" ? "" : "none";
  }

  if (recipeMealieControls) {
    recipeMealieControls.style.display = mode === "mealie" ? "" : "none";
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function createTodoItem(task = {}) {
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

  wrapper.querySelector(".todo-remove")?.addEventListener("click", () => {
    wrapper.remove();
    requestPreview({ silent: true });
  });

  wrapper.querySelectorAll("input, textarea").forEach((el) => {
    el.addEventListener("input", () => debouncePreview(750));
  });

  wrapper
    .querySelector(".todo-task-completed")
    ?.addEventListener("change", () => {
      requestPreview({ silent: true });
    });

  return wrapper;
}

function addTodoItem(task = {}) {
  if (!todoItemsContainer) return;
  todoItemsContainer.appendChild(createTodoItem(task));
}

function getTodoItems() {
  if (!todoItemsContainer) return [];

  return Array.from(todoItemsContainer.querySelectorAll(".todo-item"))
    .map((item, index) => {
      const title = item.querySelector(".todo-task-title")?.value.trim() || "";
      const labelsRaw =
        item.querySelector(".todo-task-labels")?.value.trim() || "";
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

function syncPreviewTextWidth() {
  if (!widthInput || !fontSelect) return;
  const width =
    Number(widthInput.value) || (fontSelect.value === "A" ? 48 : 56);
  document.documentElement.style.setProperty("--receipt-columns", width);
}

function updateWidthFromFont() {
  if (!widthInput || !fontSelect) return;
  const current = Number(widthInput.value);
  if (!current || current === 48 || current === 56) {
    widthInput.value = fontSelect.value === "A" ? 48 : 56;
  }
}

function setActiveVerbChip(activeVerb) {
  document.querySelectorAll(".verb-chip").forEach((chip) => {
    const isActive = chip.dataset.verb === activeVerb;
    chip.classList.toggle("is-active", isActive);
    chip.setAttribute("aria-pressed", String(isActive));
  });
}

function syncLabelVerbChipState() {
  const currentVerb = labelVerb?.value.trim() || "";
  setActiveVerbChip(currentVerb);
}

function buildRequest() {
  const moduleName = moduleSelect?.value || "notes";
  const font = fontSelect?.value || "A";
  const width = Number(widthInput?.value) || (font === "A" ? 48 : 56);

  const req = {
    module_name: moduleName,
    output_kind: "raw_tcp",
    render_config: { font, width },
    output_config: { dry_run: false },
    render_options: { ...renderOptions },
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

    req.content = importedRecipe
      ? { recipe: importedRecipe }
      : { recipe: null };
  } else if (moduleName === "todo") {
    if (todoSourceMode?.value === "donetick") {
      req.source_name = "donetick";
      req.source_options = {};

      const labelFilter = doneTickLabelSelect?.value.trim() || "";
      if (labelFilter) {
        req.source_options.label_filter = labelFilter;
      }

      const dateFilter = doneTickDateFilterSelect?.value || "";
      if (dateFilter) {
        req.source_options.date_filter = dateFilter;
      }

      req.source_options.include_overdue = !!doneTickIncludeOverdue?.checked;
    } else {
      req.content = {
        title:
          document.getElementById("todoTitle")?.value.trim() || "Todo List",
        items: getTodoItems(),
      };
    }
  } else if (moduleName === "label") {
    if (labelDate && !labelDate.value) {
      labelDate.value = new Date().toISOString().slice(0, 10);
    }

    const raw = labelDate?.value || "";
    let formatted = "";

    if (raw) {
      const [yyyy, mm, dd] = raw.split("-");
      formatted = `${mm}/${dd}/${String(yyyy).slice(2)}`;
    }

    req.content = {
      verb: labelVerb?.value.trim() || "Opened",
      date: formatted,
      note: labelNote?.value.trim() || "",
    };
    req.theme_name = labelTheme?.value || "framed_food";
  }

  console.log("request payload", req);
  return req;
}

async function loadMealieRecipes() {
  if (!loadMealieRecipesBtn || !mealieRecipeSelect) return false;

  loadMealieRecipesBtn.disabled = true;
  mealieRecipeSelect.disabled = true;
  mealieRecipeSelect.innerHTML = "";
  mealieRecipeSelect.appendChild(new Option("Loading recipes…", ""));

  try {
    const search = mealieRecipeSearch?.value.trim() || "";
    const url = new URL("/recipes/mealie");
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

    mealieRecipeSelect.innerHTML = "";
    mealieRecipeSelect.appendChild(new Option("Select a recipe", ""));

    recipes.forEach((recipe) => {
      const value = recipe.slug || recipe.id || "";
      const label = recipe.name || recipe.title || value;
      mealieRecipeSelect.appendChild(new Option(label, value));
    });

    mealieRecipeSelect.disabled = false;
    mealieRecipesLoaded = true;
    return true;
  } catch (err) {
    mealieRecipeSelect.innerHTML = "";
    mealieRecipeSelect.appendChild(new Option("Failed to load recipes", ""));
    mealieRecipeSelect.disabled = true;
    mealieRecipesLoaded = false;
    return false;
  } finally {
    loadMealieRecipesBtn.disabled = false;
  }
}

async function importRecipeFromUrl() {
  const url = recipeSourceUrl.value.trim();
  if (!url) return;

  const resp = await fetch("/recipes/import", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

  if (!resp.ok) {
    // Show a nice error; for now just log
    console.error("Import failed", await resp.json());
    return;
  }

  const data = await resp.json();
  importedRecipe = data.recipe;
}

async function importRecipeFromMealie() {
  const slug = mealieRecipeSelect?.value.trim();
  if (!slug) return;

  const res = await fetch(
    `/recipes/mealie/${encodeURIComponent(slug)}`,
  );
  if (!res.ok) {
    console.error("Mealie recipe fetch failed", await res.json());
    return;
  }

  const data = await res.json();
  importedRecipe = data.recipe;
}

async function callApi(path, payload) {
  const controller = new AbortController();
  abortController = controller;

  try {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    const contentType = res.headers.get("content-type") || "";
    const isJson = contentType.includes("application/json");
    const body = isJson ? await res.json() : await res.text();

    if (!res.ok) {
      const message = formatApiError(body, res.status);
      const error = new Error(message);
      error.details = body;
      error.status = res.status;
      throw error;
    }

    return body;
  } finally {
    if (abortController === controller) {
      abortController = null;
    }
  }
}

async function loadLabelThemes() {
  if (!labelTheme) return;

  labelTheme.disabled = true;
  labelTheme.innerHTML = '<option value="">Loading themes…</option>';

  try {
    const res = await fetch("/api/labels/themes");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();
    const themes = Array.isArray(data) ? data : [];

    labelTheme.innerHTML = "";
    themes.forEach((theme) => {
      const opt = document.createElement("option");
      opt.value = theme.value;
      opt.textContent = theme.label;
      labelTheme.appendChild(opt);
    });

    const defaultTheme = "framed_food";
    if ([...labelTheme.options].some((o) => o.value === defaultTheme)) {
      labelTheme.value = defaultTheme;
    } else {
      labelTheme.value = labelTheme.options[0]?.value || "";
    }
  } catch (err) {
    console.error("Failed to load label themes", err);
    labelTheme.innerHTML =
      '<option value="framed_food">Framed Food (default)</option>';
    labelTheme.value = "framed_food";
  } finally {
    labelTheme.disabled = false;
  }
}

function initLabelDate() {
  if (!labelDate || labelDate.value) return;

  const today = new Date();
  const yyyy = today.getFullYear();
  const mm = String(today.getMonth() + 1).padStart(2, "0");
  const dd = String(today.getDate()).padStart(2, "0");
  labelDate.value = `${yyyy}-${mm}-${dd}`;
}

function renderReceipt(data) {
  if (!previewEl && !labelPreviewImage) return;

  const moduleName = data?.module || moduleSelect?.value || "notes";

  if (moduleName === "label") {
    const imgPath = data?.gray_path || data?.bw_path;

    console.log("label preview data:", data);
    console.log("label image path:", imgPath);
    
    if (previewEl) {
      previewEl.hidden = true;
      previewEl.textContent = "";
    }

    if (labelPreviewImage) {
      labelPreviewImage.hidden = false;
      if (imgPath) {
        labelPreviewImage.src = `${imgPath}?t=${Date.now()}`;
      }
    }
  } else {
    if (labelPreviewImage) {
      labelPreviewImage.hidden = true;
      labelPreviewImage.removeAttribute("src");
    }

    if (previewEl) {
      previewEl.hidden = false;
      previewEl.textContent = data?.receipt?.text_preview || "";
    }
  }

  animateReceipt();
}

function getActivePreviewEl() {
  if (labelPreviewImage && !labelPreviewImage.hidden) return labelPreviewImage;
  return previewEl;
}

function animateReceipt() {
  const target = getActivePreviewEl();
  if (!target) return;

  target.classList.remove("is-falling-away");
  target.classList.remove("is-printing");
  void target.offsetWidth;
  target.classList.add("is-printing");
}

function animateReceiptSuccess() {
  const target = getActivePreviewEl();
  if (!target) return;

  target.classList.remove("is-printing");
  target.classList.remove("is-falling-away");
  void target.offsetWidth;
  target.classList.add("is-falling-away");
}

function animatePrintButtonSuccess() {
  const btn = printButton;
  if (!btn) return;

  btn.classList.remove("is-success");
  void btn.offsetWidth;
  btn.classList.add("is-success");
}

async function requestPreview({ silent = false } = {}) {
  if (abortController) {
    abortController.abort();
    abortController = null;
  }

  setLoading(true);

  try {
    if (moduleSelect?.value === "recipe") {
      importedRecipe = null;

      const sourceMode = recipeSourceMode?.value || "url";
      if (sourceMode === "url") {
        await importRecipeFromUrl();
      } else if (sourceMode === "mealie") {
        await importRecipeFromMealie();
      }
    }

    const req = buildRequest();
    const moduleName = req.module_name;

    // Route to the correct endpoint based on module
    let path;
    if (moduleName === "label") {
      path = "/api/labels/preview";
    } else {
      path = "/preview";
    }

    const data = await callApi(path, req);
    renderReceipt(data);
  } catch (err) {
    if (err.name === "AbortError") {
      return;
    }
    console.error(err.details || err);
  } finally {
    setLoading(false);
  }
}

async function loadDoneTickLabels() {
  if (!loadLabelsBtn || !doneTickLabelSelect) return false;

  loadLabelsBtn.disabled = true;
  doneTickLabelSelect.disabled = true;
  doneTickLabelSelect.innerHTML = "";
  doneTickLabelSelect.appendChild(new Option("Loading labels…", ""));

  try {
    const res = await fetch("/sources/donetick/labels");
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status}: ${text}`);
    }

    const data = await res.json();
    const labels = Array.isArray(data.labels) ? data.labels : [];

    doneTickLabelSelect.innerHTML = "";
    doneTickLabelSelect.appendChild(new Option("All labels", ""));
    labels.forEach((label) => {
      doneTickLabelSelect.appendChild(new Option(label, label));
    });
    doneTickLabelSelect.disabled = false;

    return true;
  } catch (err) {
    doneTickLabelSelect.innerHTML = "";
    doneTickLabelSelect.appendChild(new Option("Failed to load labels", ""));
    doneTickLabelSelect.disabled = true;
    return false;
  } finally {
    loadLabelsBtn.disabled = false;
  }
}

document.getElementById("refreshBtn")?.addEventListener("click", async () => {
  await requestPreview();
});

document.getElementById("printBtn")?.addEventListener("click", async () => {
  setLoading(true);

  try {
    if (moduleSelect?.value === "recipe") {
      importedRecipe = null;
      await importRecipeFromUrl();
    }

    const req = buildRequest();
    const moduleName = req.module_name;

    let path;
    if (moduleName === "label") {
      path = "/api/labels/print";
    } else {
      path = "/print";
    }

    const data = await callApi(path, req);

    renderReceipt(data);
    animateReceiptSuccess();
    animatePrintButtonSuccess();
  } catch (err) {
    console.error(err.details || err);
  } finally {
    setLoading(false);
  }
});

document.querySelectorAll(".verb-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    const verb = chip.dataset.verb || "Opened";
    if (labelVerb) labelVerb.value = verb;
    setActiveVerbChip(verb);
    requestPreview({ silent: true });
  });
});

document.querySelectorAll(".toggle-chip").forEach((chip) => {
  const key = chip.dataset.option;
  chip.classList.toggle("is-active", !!renderOptions[key]);
  chip.setAttribute("aria-pressed", String(!!renderOptions[key]));

  chip.addEventListener("click", () => {
    renderOptions[key] = !renderOptions[key];
    chip.classList.toggle("is-active", renderOptions[key]);
    chip.setAttribute("aria-pressed", String(renderOptions[key]));
    requestPreview({ silent: true });
  });
});

document
  .querySelectorAll(
    `
  #title,
  #body,
  #todoTitle,
  #labelVerb,
  #labelDate,
  #labelNote,
  #labelTheme,
  #recipeSourceUrl
`,
  )
  .forEach((el) => {
    el.addEventListener("input", () => {
      if (el.id === "labelVerb") {
        syncLabelVerbChipState();
      }
      debouncePreview(750);
    });
  });

document.querySelectorAll(".launch-card").forEach((card) => {
  card.addEventListener("click", () => {
    openModule(card.dataset.module, {
      todoSourceMode: card.dataset.todoSource || null,
    });
  });
});

homeBtnEl?.addEventListener("click", () => {
  setScreen("home");
});

moduleSelect?.addEventListener("change", () => {
  toggleForms();
  requestPreview({ silent: true });
});

todoSourceMode?.addEventListener("change", () => {
  toggleTodoSourceMode();
  requestPreview({ silent: true });
});

loadLabelsBtn?.addEventListener("click", loadDoneTickLabels);

doneTickLabelSelect?.addEventListener("change", () => {
  requestPreview({ silent: true });
});

doneTickIncludeOverdue?.addEventListener("change", () => {
  requestPreview({ silent: true });
});

doneTickDateFilterSelect?.addEventListener("change", () => {
  syncDateFilterControls();
  requestPreview({ silent: true });
});

recipeSourceMode?.addEventListener("change", async () => {
  toggleRecipeSourceMode();

  if (recipeSourceMode.value === "mealie" && !mealieRecipesLoaded) {
    await loadMealieRecipes();
  }

  requestPreview({ silent: true });
});

loadMealieRecipesBtn?.addEventListener("click", async () => {
  await loadMealieRecipes();
});

mealieRecipeSearch?.addEventListener("input", () => {
  window.clearTimeout(previewDebounceTimer);
  previewDebounceTimer = window.setTimeout(() => {
    loadMealieRecipes();
  }, 500);
});

mealieRecipeSelect?.addEventListener("change", () => {
  requestPreview({ silent: true });
});

fontSelect?.addEventListener("change", () => {
  updateWidthFromFont();
  syncPreviewTextWidth();
  requestPreview({ silent: true });
});

widthInput?.addEventListener("input", () => {
  syncPreviewTextWidth();
  requestPreview({ silent: true });
});

addTaskBtn?.addEventListener("click", () => {
  addTodoItem();
  requestPreview({ silent: true });
});

labelVerb?.addEventListener("input", () => {
  syncLabelVerbChipState();
});

labelTheme?.addEventListener("change", () => {
  requestPreview({ silent: true });
});

if (todoItemsContainer && !todoItemsContainer.children.length) {
  addTodoItem({
    title: "Buy milk",
    completed: false,
    labels: ["Errands"],
    description: "",
  });
  addTodoItem({
    title: "Call plumber",
    completed: false,
    labels: ["House Maintenance"],
    description: "",
  });
}

initLabelDate();
loadLabelThemes();
syncDateFilterControls();
syncLabelVerbChipState();
syncPreviewTextWidth();
setScreen("home");
toggleForms();
updateWidthFromFont();