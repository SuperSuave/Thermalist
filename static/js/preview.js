import { els } from "./state.js";

export function getActivePreviewEl() {
  if (els.labelPreviewImage && !els.labelPreviewImage.hidden) {
    return els.labelPreviewImage;
  }
  return els.previewEl;
}

export function animateReceipt() {
  const target = getActivePreviewEl();
  if (!target) return;

  target.classList.remove("is-falling-away");
  target.classList.remove("is-printing");
  void target.offsetWidth;
  target.classList.add("is-printing");
}

export function animateReceiptSuccess() {
  const target = getActivePreviewEl();
  if (!target) return;

  target.classList.remove("is-printing");
  target.classList.remove("is-falling-away");
  void target.offsetWidth;
  target.classList.add("is-falling-away");
}

export function animatePrintButtonSuccess() {
  const btn = els.printButton;
  if (!btn) return;

  btn.classList.remove("is-success");
  void btn.offsetWidth;
  btn.classList.add("is-success");
}

export function renderReceipt(data, moduleNameOverride = null) {
  if (!els.previewEl && !els.labelPreviewImage) return;

  const moduleName = moduleNameOverride || data?.module || els.moduleSelect?.value || "notes";

  if (moduleName === "label") {
    const imgPath = data?.gray_path || data?.bw_path;

    if (els.previewEl) {
      els.previewEl.hidden = true;
      els.previewEl.textContent = "";
    }

    if (els.labelPreviewImage) {
      els.labelPreviewImage.hidden = false;

      if (imgPath) {
        els.labelPreviewImage.src = `${imgPath}?t=${Date.now()}`;
      } else {
        els.labelPreviewImage.removeAttribute("src");
      }
    }
  } else {
    if (els.labelPreviewImage) {
      els.labelPreviewImage.hidden = true;
      els.labelPreviewImage.removeAttribute("src");
    }

    if (els.previewEl) {
      els.previewEl.hidden = false;
      els.previewEl.textContent = data?.receipt?.text_preview || "";
    }
  }

  animateReceipt();
}