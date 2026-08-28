import {
  state,
  els,
  setScreen,
  debouncePreview,
  setLoading,
  hideError,
  showError,
} from "./state.js";

import { callApi, abortActiveRequest } from "./api.js";

import {
  toggleForms,
  openModule,
  syncDateFilterControls,
  syncPreviewTextWidth,
  updateWidthFromFont,
  syncLabelVerbChipState,
  setActiveVerbChip,
  addTodoItem,
  loadDoneTickLabels,
  loadMealieRecipes,
  importRecipeFromUrl,
  importRecipeFromMealie,
  loadLabelThemes,
  initLabelDate,
  buildRequest,
  toggleTodoSourceMode,
  toggleRecipeSourceMode,
} from "./modules.js";

import {
  renderReceipt,
  animateReceiptSuccess,
  animatePrintButtonSuccess,
} from "./preview.js";

async function requestPreview({ silent = false } = {}) {
  abortActiveRequest();

  const requestId = ++state.latestPreviewRequestId;
  hideError();
  setLoading(true);

  try {
    if (els.moduleSelect?.value === "recipe") {
      if (!state.recipeLoadAttempted) {
        return;
      }

      state.importedRecipe = null;

      const sourceMode = els.recipeSourceMode?.value || "url";
      if (sourceMode === "url") {
        await importRecipeFromUrl();
      } else if (sourceMode === "mealie") {
        await importRecipeFromMealie();
      }
    }

    const req = buildRequest();
    const moduleName = req.module_name;
    const path = moduleName === "label" ? "/api/labels/preview" : "/preview";

    const data = await callApi(path, req);

    if (requestId !== state.latestPreviewRequestId) {
      return;
    }

    renderReceipt(data, moduleName);
  } catch (err) {
    if (err.name === "AbortError") {
      return;
    }

    showError(
      `Preview failed for ${els.moduleSelect?.value || "current module"}.`,
      err.details || err.message || String(err)
    );

    if (!silent) {
      console.error(err.details || err);
    }
  } finally {
    if (requestId === state.latestPreviewRequestId) {
      setLoading(false);
    }
  }
}

async function handlePrint() {
  hideError();
  setLoading(true);

  try {
    if (els.moduleSelect?.value === "recipe") {
      state.importedRecipe = null;

      const sourceMode = els.recipeSourceMode?.value || "url";
      if (sourceMode === "url") {
        await importRecipeFromUrl();
      } else if (sourceMode === "mealie") {
        await importRecipeFromMealie();
      }
    }

    const req = buildRequest();
    const moduleName = req.module_name;
    const path = moduleName === "label" ? "/api/labels/print" : "/print";

    const data = await callApi(path, req);

    renderReceipt(data, moduleName);
    animateReceiptSuccess();
    animatePrintButtonSuccess();
  } catch (err) {
    showError(
      `Print failed for ${els.moduleSelect?.value || "current module"}.`,
      err.details || err.message || String(err)
    );
    console.error(err.details || err);
  } finally {
    setLoading(false);
  }
}

function bindStaticEvents() {
  document.getElementById("refreshBtn")?.addEventListener("click", async () => {
    if (els.moduleSelect?.value === "recipe") {
      state.recipeLoadAttempted = true;
    }
    await requestPreview();
  });

  document.getElementById("printBtn")?.addEventListener("click", async () => {
    if (els.moduleSelect?.value === "recipe") {
      state.recipeLoadAttempted = true;
    }
    await handlePrint();
  });

  document.querySelectorAll(".verb-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const verb = chip.dataset.verb || "Opened";
      if (els.labelVerb) els.labelVerb.value = verb;
      setActiveVerbChip(verb);
      requestPreview({ silent: true });
    });
  });

  document.querySelectorAll(".toggle-chip").forEach((chip) => {
    const key = chip.dataset.option;
    chip.classList.toggle("is-active", !!state.renderOptions[key]);
    chip.setAttribute("aria-pressed", String(!!state.renderOptions[key]));

    chip.addEventListener("click", () => {
      state.renderOptions[key] = !state.renderOptions[key];
      chip.classList.toggle("is-active", state.renderOptions[key]);
      chip.setAttribute("aria-pressed", String(state.renderOptions[key]));
      requestPreview({ silent: true });
    });
  });

  document
    .querySelectorAll(`
      #title,
      #body,
      #todoTitle,
      #labelVerb,
      #labelDate,
      #labelNote,
      #labelTheme,
      #recipeSourceUrl
    `)
    .forEach((el) => {
      el.addEventListener("input", () => {
        if (el.id === "labelVerb") {
          syncLabelVerbChipState();
        }
        debouncePreview(() => requestPreview({ silent: true }), 750);
      });
    });

  document.querySelectorAll(".launch-card").forEach((card) => {
    card.addEventListener("click", () => {
      openModule(card.dataset.module, {
        todoSourceMode: card.dataset.todoSource || null,
      });
      requestPreview({ silent: true });
    });
  });

  els.homeBtnEl?.addEventListener("click", () => {
    setScreen("home");
  });

  els.moduleSelect?.addEventListener("change", () => {
    if (els.moduleSelect.value !== "recipe") {
      state.recipeLoadAttempted = false;
      state.recipeFieldTouched = false;
    }
    toggleForms();
    requestPreview({ silent: true });
  });

  els.todoSourceMode?.addEventListener("change", () => {
    toggleTodoSourceMode();
    requestPreview({ silent: true });
  });

  els.loadLabelsBtn?.addEventListener("click", async () => {
    state.doneTickLabelsLoaded = await loadDoneTickLabels();
  });

  els.doneTickLabelSelect?.addEventListener("change", () => {
    requestPreview({ silent: true });
  });

  els.doneTickIncludeOverdue?.addEventListener("change", () => {
    requestPreview({ silent: true });
  });

  els.doneTickDateFilterSelect?.addEventListener("change", () => {
    syncDateFilterControls();
    requestPreview({ silent: true });
  });

  els.recipeSourceMode?.addEventListener("change", async () => {
    state.recipeLoadAttempted = false;
    hideError();
    toggleRecipeSourceMode();

    if (els.recipeSourceMode.value === "mealie" && !state.mealieRecipesLoaded) {
      await loadMealieRecipes();
    }

    requestPreview({ silent: true });
  });

  els.recipeSourceUrl?.addEventListener("input", () => {
    state.recipeFieldTouched = true;
  });

  els.loadMealieRecipesBtn?.addEventListener("click", async () => {
    hideError();
    state.recipeLoadAttempted = true;
    const ok = await loadMealieRecipes();
    if (!ok) {
      showError("Failed to load Mealie recipes.");
    }
  });

  els.mealieRecipeSearch?.addEventListener("input", () => {
    debouncePreview(() => {
      loadMealieRecipes();
    }, 500);
  });

  els.mealieRecipeSelect?.addEventListener("change", () => {
    state.recipeLoadAttempted = true;
    requestPreview({ silent: true });
  });

  els.fontSelect?.addEventListener("change", () => {
    updateWidthFromFont();
    syncPreviewTextWidth();
    requestPreview({ silent: true });
  });

  els.widthInput?.addEventListener("input", () => {
    syncPreviewTextWidth();
    requestPreview({ silent: true });
  });

  els.addTaskBtn?.addEventListener("click", () => {
    addTodoItem();
    bindTodoItemEventsForLatest();
    requestPreview({ silent: true });
  });

  els.labelVerb?.addEventListener("input", () => {
    syncLabelVerbChipState();
  });

  els.labelTheme?.addEventListener("change", () => {
    requestPreview({ silent: true });
  });

  els.errorDismissBtn?.addEventListener("click", () => {
    hideError();
  });

}

function bindTodoItemEventsForLatest() {
  const lastItem = els.todoItemsContainer?.lastElementChild;
  if (!lastItem) return;

  lastItem.querySelector(".todo-remove")?.addEventListener("click", () => {
    lastItem.remove();
    requestPreview({ silent: true });
  });

  lastItem.querySelectorAll("input, textarea").forEach((el) => {
    el.addEventListener("input", () => {
      debouncePreview(() => requestPreview({ silent: true }), 750);
    });
  });

  lastItem.querySelector(".todo-task-completed")?.addEventListener("change", () => {
    requestPreview({ silent: true });
  });
}

function seedInitialTodoItems() {
  if (!els.todoItemsContainer || els.todoItemsContainer.children.length) return;

  addTodoItem({
    title: "Buy milk",
    completed: false,
    labels: ["Errands"],
    description: "",
  });
  bindTodoItemEventsForLatest();

  addTodoItem({
    title: "Call plumber",
    completed: false,
    labels: ["House Maintenance"],
    description: "",
  });
  bindTodoItemEventsForLatest();
}

function init() {
  initLabelDate();
  loadLabelThemes();
  syncDateFilterControls();
  syncLabelVerbChipState();
  syncPreviewTextWidth();
  setScreen("home");
  toggleForms();
  updateWidthFromFont();
  seedInitialTodoItems();
  bindStaticEvents();
}

state.latestPreviewRequestId = 0;

init();