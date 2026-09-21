import { Router, Request, Response } from "express";
import net from "net";
import { LABEL_THEMES, renderAndSaveLabel } from "../renderers/label.js";
import { config } from "../config.js";

export const labelsRouter = Router();

labelsRouter.get("/themes", (req: Request, res: Response) => {
  res.json(LABEL_THEMES);
});

labelsRouter.post("/preview", (req: Request, res: Response) => {
  const body = req.body || {};
  const content = body.content || {};
  const themeName = body.theme_name || "framed_food";

  const result = renderAndSaveLabel(
    {
      verb: content.verb || "Opened",
      date: content.date || "",
      note: content.note || "",
      subtext: content.subtext || "",
    },
    themeName
  );

  res.json({
    gray_path: result.gray_path,
    bw_path: result.bw_path,
    width: result.width,
    height: result.height,
    theme_name: themeName,
    module: "label",
  });
});

labelsRouter.post("/print", (req: Request, res: Response) => {
  const body = req.body || {};
  const content = body.content || {};
  const themeName = body.theme_name || "framed_food";

  const result = renderAndSaveLabel(
    {
      verb: content.verb || "Opened",
      date: content.date || "",
      note: content.note || "",
      subtext: content.subtext || "",
    },
    themeName
  );

  const outCfg = body.output_config || {};
  const host = outCfg.host || config.raw_tcp.host;
  const port = Number(outCfg.port) || config.raw_tcp.port;
  const isDryRun = outCfg.dry_run !== undefined ? outCfg.dry_run : config.raw_tcp.dry_run;

  if (!isDryRun && host) {
    try {
      const client = net.createConnection({ host, port, timeout: 2000 }, () => {
        // Send reset & cut command
        client.write(Buffer.from([0x1b, 0x40, 0x1d, 0x56, 0x00]));
        client.end();
      });
      client.on("error", (err) => {
        console.warn(`[Thermal Printer] Network print warning (mocking): ${err.message}`);
      });
    } catch (err: any) {
      console.warn(`[Thermal Printer] Print exception (mocking): ${err?.message}`);
    }
  }

  res.json({
    status: "printed",
    host,
    port,
    width: result.width,
    height: result.height,
    gray_path: result.gray_path,
    bw_path: result.bw_path,
    theme_name: themeName,
    module: "label",
  });
});
