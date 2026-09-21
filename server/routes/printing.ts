import { Router, Request, Response } from "express";
import net from "net";
import { Receipt80mmRenderer } from "../renderers/receipt.js";
import { buildDocumentFromRequest, fetchDoneTickTasks } from "./preview.js";
import { config } from "../config.js";

export const printingRouter = Router();

printingRouter.post("", async (req: Request, res: Response) => {
  const body = req.body || {};
  const moduleName = body.module_name || "notes";
  const renderConfig = body.render_config || {};
  const renderOptions = {
    ...(body.render_options || {}),
    ...(body.module_options || {}),
  };

  const font = renderConfig.font || "A";
  const width = Number(renderConfig.width) || (font === "A" ? 48 : 56);

  let tasks: any[] = [];
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
      tasks = body.content?.items || [];
    }
  }

  const document = buildDocumentFromRequest(moduleName, body.content, tasks, renderOptions);
  const renderer = new Receipt80mmRenderer(width, renderOptions.show_due !== false);
  const receipt = renderer.render(document);

  const outCfg = body.output_config || {};
  const host = outCfg.host || config.raw_tcp.host;
  const port = Number(outCfg.port) || config.raw_tcp.port;
  const isDryRun = outCfg.dry_run !== undefined ? outCfg.dry_run : config.raw_tcp.dry_run;

  if (!isDryRun && host) {
    try {
      const client = net.createConnection({ host, port, timeout: 2000 }, () => {
        // Initialize printer (ESC @)
        client.write(Buffer.from([0x1b, 0x40]));
        // Send receipt text encoded in ASCII/CP437
        client.write(receipt.text_preview, "latin1");
        // Feed & cut (GS V 0)
        client.write(Buffer.from([0x0a, 0x0a, 0x0a, 0x1d, 0x56, 0x00]));
        client.end();
      });
      client.on("error", (err) => {
        console.warn(`[Thermal Printer] Network print warning (mocking): ${err.message}`);
      });
    } catch (err: any) {
      console.warn(`[Thermal Printer] Print exception: ${err?.message}`);
    }
  }

  return res.json({
    status: "ok",
    backend: "raw_tcp",
    preview: receipt.text_preview,
    source: resolvedSource,
    module: moduleName,
    document,
  });
});
