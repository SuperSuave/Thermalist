export const state = {
  abortController: null,
  doneTickLabelsLoaded: false,
  previewDebounceTimer: null,
  mealieRecipesLoaded: false,
  importedRecipe: null,
  selectedMealieRecipe: null,
  renderOptions: {
    show_labels: true,
    show_due: true,
    show_description: true,
    show_subtasks: true,
    },
  latestPreviewRequestId: 0,

  recipeLoadAttempted: false,
  recipeFieldTouched: false,

};

export const els = {
  appEl: document.getElementById("app"),
  sidebarEl: document.getElementById("sidebar"),
  homeScreenEl: document.getElementById("homeScreen"),
  previewPanelEl: document.getElementById("previewPanel"),
  homeBtnEl: document.getElementById("homeBtn"),
  receiptPaper: document.querySelector(".receipt-paper"),
  printButton: document.getElementById("printBtn"),

  moduleSelect: document.getElementById("module"),
  notesForm: document.getElementById("notesForm"),
  previewEl: document.getElementById("preview"),
  fontSelect: document.getElementById("font"),
  widthInput: document.getElementById("width"),

  manualTodoControls: document.getElementById("manualTodoControls"),
  optionsSection: document.getElementById("optionsSection"),
  todoSourceMode: document.getElementById("todoSourceMode"),
  todoItemsContainer: document.getElementById("todoItemsContainer"),
  addTaskBtn: document.getElementById("addTaskBtn"),
  todoForm: document.getElementById("todoForm"),

  doneTickLabelSelect: document.getElementById("doneTickLabelSelect"),
  doneTickControls: document.getElementById("doneTickControls"),
  doneTickDateFilterSelect: document.getElementById("doneTickDateFilterSelect"),
  doneTickIncludeOverdueWrap: document.getElementById("doneTickIncludeOverdueWrap"),
  doneTickIncludeOverdue: document.getElementById("doneTickIncludeOverdue"),
  loadLabelsBtn: document.getElementById("loadLabelsBtn"),

  labelDate: document.getElementById("labelDate"),
  labelForm: document.getElementById("labelForm"),
  labelNote: document.getElementById("labelNote"),
  labelVerb: document.getElementById("labelVerb"),
  labelPreviewImage: document.getElementById("labelPreviewImage"),
  labelTheme: document.getElementById("labelTheme"),

  recipeForm: document.getElementById("recipeForm"),
  recipeSourceUrl: document.getElementById("recipeSourceUrl"),
  recipeSourceMode: document.getElementById("recipeSourceMode"),
  recipeUrlControls: document.getElementById("recipeUrlControls"),
  recipeMealieControls: document.getElementById("recipeMealieControls"),
  mealieRecipeSearch: document.getElementById("mealieRecipeSearch"),
  mealieRecipeSelect: document.getElementById("mealieRecipeSelect"),
  loadMealieRecipesBtn: document.getElementById("loadMealieRecipesBtn"),

  errorPanel: document.getElementById("errorPanel"),
  errorMessage: document.getElementById("errorMessage"),
  errorDetails: document.getElementById("errorDetails"),
  errorDismissBtn: document.getElementById("errorDismissBtn"),
};

export function setScreen(mode) {
  const isHome = mode === "home";

  if (els.homeScreenEl) {
    els.homeScreenEl.hidden = !isHome;
    els.homeScreenEl.inert = !isHome;
  }

  if (els.sidebarEl) {
    els.sidebarEl.hidden = isHome;
    els.sidebarEl.inert = isHome;
  }

  if (els.previewPanelEl) {
    els.previewPanelEl.hidden = isHome;
    els.previewPanelEl.inert = isHome;
  }

  els.appEl?.classList.toggle("is-home", isHome);
  els.appEl?.classList.toggle("is-editor", !isHome);
}

export function showHomeScreen() {
  setScreen("home");
}

export function showEditor() {
  setScreen("editor");
}

export function debouncePreview(callback, delay = 750) {
  window.clearTimeout(state.previewDebounceTimer);
  state.previewDebounceTimer = window.setTimeout(callback, delay);
}

export function setDisabledById(id, isLoading) {
  const el = document.getElementById(id);
  if (el) el.disabled = isLoading;
}

export function setLoading(isLoading) {
  setDisabledById("refreshBtn", isLoading);
  setDisabledById("printBtn", isLoading);

  if (els.moduleSelect) els.moduleSelect.disabled = isLoading;
  if (els.recipeSourceUrl) els.recipeSourceUrl.disabled = isLoading;
  if (els.addTaskBtn) els.addTaskBtn.disabled = isLoading;
  if (els.todoSourceMode) els.todoSourceMode.disabled = isLoading;
  if (els.loadLabelsBtn) els.loadLabelsBtn.disabled = isLoading;
  if (els.doneTickLabelSelect) els.doneTickLabelSelect.disabled = isLoading;
  if (els.doneTickDateFilterSelect) els.doneTickDateFilterSelect.disabled = isLoading;
  if (els.doneTickIncludeOverdue) els.doneTickIncludeOverdue.disabled = isLoading;
  if (els.fontSelect) els.fontSelect.disabled = isLoading;
  if (els.widthInput) els.widthInput.disabled = isLoading;
  if (els.labelVerb) els.labelVerb.disabled = isLoading;
  if (els.labelDate) els.labelDate.disabled = isLoading;
  if (els.labelNote) els.labelNote.disabled = isLoading;
  if (els.labelTheme) els.labelTheme.disabled = isLoading;

  els.todoItemsContainer?.querySelectorAll("input, textarea, button").forEach((el) => {
    el.disabled = isLoading;
  });

  document.querySelectorAll(".verb-chip").forEach((chip) => {
    chip.disabled = isLoading;
  });

  els.labelForm?.classList.toggle("is-loading", isLoading);
}

export function hideError() {
  if (els.errorPanel) els.errorPanel.hidden = true;
  if (els.errorMessage) els.errorMessage.textContent = "";
  if (els.errorDetails) {
    els.errorDetails.hidden = true;
    els.errorDetails.textContent = "";
  }
}

export function showError(message, details = null) {
  if (!els.errorPanel || !els.errorMessage || !els.errorDetails) return;

  els.errorMessage.textContent = message || "Something went wrong.";
  els.errorPanel.hidden = false;

  if (details) {
    els.errorDetails.hidden = false;
    els.errorDetails.textContent =
      typeof details === "string" ? details : JSON.stringify(details, null, 2);
  } else {
    els.errorDetails.hidden = true;
    els.errorDetails.textContent = "";
  }
}