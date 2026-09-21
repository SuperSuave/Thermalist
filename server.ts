import express, { Request, Response } from "express";
import cors from "cors";
import path from "path";
import fs from "fs";
import { config } from "./server/config.js";
import { labelsRouter } from "./server/routes/labels.js";
import { previewRouter } from "./server/routes/preview.js";
import { printingRouter } from "./server/routes/printing.js";
import { donetickRouter } from "./server/routes/donetick.js";
import { recipesRouter } from "./server/routes/recipes.js";
import { mcpRouter } from "./server/services/mcpServer.js";
import { renderAndSaveLabel } from "./server/renderers/label.js";

const app = express();
const PORT = config.port || 3000;

app.use(cors());
app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true }));

// Ensure generated_images directory exists and create initial label previews
const generatedImagesDir = path.join(process.cwd(), "generated_images");
if (!fs.existsSync(generatedImagesDir)) {
  fs.mkdirSync(generatedImagesDir, { recursive: true });
}
renderAndSaveLabel({ verb: "Opened", date: "09/11/26", note: "Salsa Verde Jar" }, "framed_food");

// Health check endpoints
app.get("/health", (req: Request, res: Response) => {
  res.json({ status: "ok" });
});
app.get("/api/health", (req: Request, res: Response) => {
  res.json({ status: "ok" });
});

// Primary API routers
app.use("/api/labels", labelsRouter);
app.use("/preview", previewRouter);
app.use("/print", printingRouter);
app.use(donetickRouter);
app.use("/recipes", recipesRouter);
app.use("/mcp", mcpRouter);

// Static assets and previews
const staticDir = path.join(process.cwd(), "static");
app.use("/static", express.static(staticDir));
app.use("/generated_images", express.static(generatedImagesDir));

// App root
app.get("/", (req: Request, res: Response) => {
  res.sendFile(path.join(staticDir, "index.html"));
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`ThermaList server running on http://0.0.0.0:${PORT}`);
});
