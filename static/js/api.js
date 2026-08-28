import { state } from "./state.js";

export function formatApiError(payload, status) {
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

  if (payload.message) {
    return payload.message;
  }

  return `HTTP ${status}`;
}

export async function callApi(path, payload) {
  const controller = new AbortController();
  state.abortController = controller;

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
    if (state.abortController === controller) {
      state.abortController = null;
    }
  }
}

export function abortActiveRequest() {
  if (state.abortController) {
    state.abortController.abort();
    state.abortController = null;
  }
}