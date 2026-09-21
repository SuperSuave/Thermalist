import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { Request, Response, Router } from "express";
import { Receipt80mmRenderer, TaskItem, DocumentModel } from "../renderers/receipt.js";
import { renderUnboundedGraphicSvg, saveGraphicOutput } from "./unboundedGraphicRenderer.js";
import { fetchDoneTickTasks } from "../routes/preview.js";
import { SAMPLE_RECIPES } from "../routes/recipes.js";
import { config } from "../config.js";
import net from "net";

export const mcpRouter = Router();

// Create MCP Server instance
const mcpServer = new Server(
  {
    name: "thermalist-mcp-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Define available tools
mcpServer.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "print_thermal_document",
        description: "Generate and print or preview a thermal printer document (notes, checklists, todo lists, or recipes) with professional graphic themes (framed_food, reminders_notebook, minimal, bold, playful, receipt_mono).",
        inputSchema: {
          type: "object",
          properties: {
            module_name: {
              type: "string",
              enum: ["notes", "todo", "recipes"],
              description: "The type of document module to render",
            },
            theme_name: {
              type: "string",
              enum: ["framed_food", "reminders_notebook", "minimal", "bold", "playful", "receipt_mono"],
              description: "Visual theme style for the thermal printout",
            },
            title: {
              type: "string",
              description: "Main title for the document",
            },
            body: {
              type: "string",
              description: "Text body for 'notes' module",
            },
            items: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  title: { type: "string" },
                  completed: { type: "boolean" },
                  description: { type: "string" },
                  due: { type: "string" },
                },
              },
              description: "Task items for 'todo' module",
            },
            recipe_id: {
              type: "string",
              description: "Recipe identifier for 'recipes' module (e.g. chocolate-chip-cookies)",
            },
            execute_print: {
              type: "boolean",
              description: "If true, send directly to physical TCP thermal printer if configured. If false, only generate preview and render.",
            },
          },
          required: ["module_name", "title"],
        },
      },
      {
        name: "get_tasks_list",
        description: "Fetch and list active tasks from the connected Donetick task source or sample database.",
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
      {
        name: "list_recipes",
        description: "List available recipes that can be printed or viewed.",
        inputSchema: {
          type: "object",
          properties: {
            search: {
              type: "string",
              description: "Optional search query",
            },
          },
        },
      },
    ],
  };
});

// Handle tool execution
async function executeMcpTool(name: string, args: Record<string, any>) {
  const typedArgs = (args || {}) as Record<string, any>;

  if (name === "get_tasks_list") {
    try {
      const tasks = await fetchDoneTickTasks();
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({ success: true, count: tasks.length, tasks }, null, 2),
          },
        ],
      };
    } catch (err: any) {
      return {
        content: [{ type: "text", text: JSON.stringify({ success: false, error: err?.message }) }],
        isError: true,
      };
    }
  }

  if (name === "list_recipes") {
    const search = (typedArgs.search || "").toLowerCase();
    const recipes = Object.values(SAMPLE_RECIPES)
      .filter((r) => !search || r.title.toLowerCase().includes(search))
      .map((r) => ({ id: r.id, name: r.title, prep: r.prep_time, cook: r.cook_time }));

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({ success: true, count: recipes.length, recipes }, null, 2),
        },
      ],
    };
  }

  if (name === "print_thermal_document") {
    const moduleName = typedArgs.module_name || "notes";
    const themeName = typedArgs.theme_name || "framed_food";
    const title = typedArgs.title || "Thermal Print";
    const executePrint = !!typedArgs.execute_print;

    let docModel: DocumentModel;
    let graphicRes: { svg: string; width: number; height: number };

    if (moduleName === "notes") {
      const body = typedArgs.body || "";
      docModel = {
        title,
        sections: [
          { kind: "title", text: title },
          { kind: "text", text: body },
        ],
        metadata: { module: "notes" },
      };
      graphicRes = renderUnboundedGraphicSvg({
        themeName,
        title,
        noteBody: body,
      });
    } else if (moduleName === "todo") {
      const rawItems = typedArgs.items || [
        { title: "Review MCP request", completed: false },
        { title: "Test thermal printer connection", completed: true },
      ];
      const items: TaskItem[] = rawItems.map((item: any, idx: number) => ({
        id: String(idx + 1),
        title: item.title || "Task",
        completed: !!item.completed,
        description: item.description || "",
        due: item.due || null,
        labels: ["General"],
      }));

      docModel = {
        title,
        sections: [
          { kind: "title", text: title },
          { kind: "task_list", tasks: items },
        ],
        metadata: { module: "todo" },
      };
      graphicRes = renderUnboundedGraphicSvg({
        themeName,
        title,
        items,
      });
    } else if (moduleName === "recipes") {
      const recipeId = typedArgs.recipe_id || "chocolate-chip-cookies";
      const r = SAMPLE_RECIPES[recipeId] || SAMPLE_RECIPES["chocolate-chip-cookies"];

      docModel = {
        title: r.title,
        sections: [
          { kind: "title", text: r.title },
          { kind: "text", text: r.description },
          { kind: "text", text: `Prep: ${r.prep_time} | Cook: ${r.cook_time}` },
        ],
        metadata: { module: "recipes" },
      };
      graphicRes = renderUnboundedGraphicSvg({
        themeName,
        title: r.title,
        recipe: {
          title: r.title,
          description: r.description,
          prepTime: r.prep_time,
          cookTime: r.cook_time,
          servings: String(r.servings || 4),
          ingredients: r.ingredients.map((i) => i.text),
          instructions: r.steps.map((s) => s.text),
        },
      });
    } else {
      throw new Error(`Unknown module name: ${moduleName}`);
    }

    const renderer = new Receipt80mmRenderer(48, true);
    const receipt = renderer.render(docModel);
    const receiptText = receipt.text_preview;
    const filename = `${moduleName}_${Date.now()}.svg`;
    const imagePath = saveGraphicOutput(filename, graphicRes.svg);

    let printResult = { sent: false, message: "Dry run preview generated successfully" };
    if (executePrint) {
      try {
        const host = config.raw_tcp.host;
        const port = config.raw_tcp.port;
        if (host) {
          await new Promise<void>((resolve, reject) => {
            const client = net.createConnection({ host, port, timeout: 2000 }, () => {
              client.write(Buffer.from([0x1b, 0x40]));
              client.write(receiptText, "latin1");
              client.write(Buffer.from([0x0a, 0x0a, 0x0a, 0x1d, 0x56, 0x00]));
              client.end();
              resolve();
            });
            client.on("error", (err) => reject(err));
          });
          printResult = { sent: true, message: "Successfully sent to physical TCP thermal printer!" };
        } else {
          printResult = { sent: false, message: "No TCP printer host configured" };
        }
      } catch (err: any) {
        printResult = { sent: false, message: `Failed to print to TCP printer: ${err?.message}` };
      }
    }

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              success: true,
              module: moduleName,
              theme: themeName,
              preview_image: imagePath,
              receipt_preview: receiptText,
              printer_status: printResult,
            },
            null,
            2
          ),
        },
      ],
    };
  }

  throw new Error(`Unknown tool: ${name}`);
}

mcpServer.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  return await executeMcpTool(name, (args || {}) as Record<string, any>);
});

// SSE Transport for MCP clients (like Google Spark / Claude / MCP inspectors)
let activeTransport: SSEServerTransport | null = null;

mcpRouter.get("/sse", async (req: Request, res: Response) => {
  const transport = new SSEServerTransport("/mcp/messages", res);
  activeTransport = transport;
  await mcpServer.connect(transport);
});

mcpRouter.post("/messages", async (req: Request, res: Response) => {
  if (activeTransport) {
    await activeTransport.handlePostMessage(req, res);
  } else {
    res.status(400).send("No active SSE transport session");
  }
});

// Direct REST/JSON invocation endpoint for agents & webhooks
mcpRouter.post("/invoke", async (req: Request, res: Response) => {
  try {
    const { tool, arguments: args } = req.body || {};
    if (!tool) {
      return res.status(400).json({ error: "Missing 'tool' name in request body" });
    }
    const result = await executeMcpTool(tool, args || {});
    return res.json(result);
  } catch (err: any) {
    return res.status(500).json({ error: err?.message || "Tool execution failed" });
  }
});
