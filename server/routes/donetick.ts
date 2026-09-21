import { Router, Request, Response } from "express";
import { fetchDoneTickTasks, SAMPLE_DONETICK_TASKS } from "./preview.js";

export const donetickRouter = Router();

donetickRouter.get("/sources/donetick/labels", async (req: Request, res: Response) => {
  try {
    const tasks = await fetchDoneTickTasks();
    const labelSet = new Set<string>();

    for (const task of tasks) {
      if (Array.isArray(task.labels)) {
        for (const l of task.labels) {
          if (l && typeof l === "string" && l.trim()) {
            labelSet.add(l.trim());
          }
        }
      }
    }

    if (labelSet.size === 0) {
      for (const task of SAMPLE_DONETICK_TASKS) {
        task.labels?.forEach((l) => labelSet.add(l));
      }
    }

    const labels = Array.from(labelSet).sort((a, b) => a.localeCompare(b, undefined, { sensitivity: "base" }));

    res.json({
      ok: true,
      labels,
      count: labels.length,
    });
  } catch (err: any) {
    res.status(502).json({
      ok: false,
      error: err?.message || "Failed to load DoneTick labels",
    });
  }
});
