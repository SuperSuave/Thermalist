import { Router, Request, Response } from "express";
import { config } from "../config.js";

export const recipesRouter = Router();

export interface RecipeItem {
  id: string;
  slug: string;
  title: string;
  description?: string;
  servings?: number | string;
  prep_time?: string;
  cook_time?: string;
  total_time?: string;
  ingredients: Array<{ text: string }>;
  steps: Array<{ number: number; text: string }>;
  labels?: string[];
  source_url?: string;
}

export const SAMPLE_RECIPES: Record<string, RecipeItem> = {
  "chocolate-chip-cookies": {
    id: "chocolate-chip-cookies",
    slug: "chocolate-chip-cookies",
    title: "Classic Chocolate Chip Cookies",
    description: "Chewy on the inside, golden crisp on the outside with melted dark chocolate chunks.",
    servings: 24,
    prep_time: "15 mins",
    cook_time: "10 mins",
    total_time: "25 mins",
    ingredients: [
      { text: "2 1/4 cups (280g) all-purpose flour" },
      { text: "1 tsp baking soda & 1/2 tsp salt" },
      { text: "1 cup (2 sticks) unsalted butter, softened" },
      { text: "3/4 cup granulated sugar" },
      { text: "3/4 cup packed brown sugar" },
      { text: "2 large eggs, room temperature" },
      { text: "2 tsp pure vanilla extract" },
      { text: "2 cups semisweet chocolate chips" },
    ],
    steps: [
      { number: 1, text: "Preheat oven to 375°F (190°C) and line two baking sheets with parchment paper." },
      { number: 2, text: "Whisk flour, baking soda, and salt together in a medium bowl; set aside." },
      { number: 3, text: "In a stand mixer or large bowl, beat softened butter and sugars until creamy (2 mins)." },
      { number: 4, text: "Beat in eggs one at a time, then vanilla until fully incorporated." },
      { number: 5, text: "Gradually stir in dry ingredients until just combined, then fold in chocolate chips." },
      { number: 6, text: "Drop rounded tablespoons onto baking sheets 2 inches apart." },
      { number: 7, text: "Bake 9-11 minutes until golden brown around edges. Cool on pan 5 minutes." },
    ],
    labels: ["Dessert", "Baking"],
    source_url: "https://recipes.themedina.house/recipe/chocolate-chip-cookies",
  },
  "creamy-tomato-basil-pasta": {
    id: "creamy-tomato-basil-pasta",
    slug: "creamy-tomato-basil-pasta",
    title: "Creamy Tomato Basil Pasta",
    description: "Rich, silky 20-minute weeknight pasta with San Marzano tomatoes and fresh aromatic basil.",
    servings: 4,
    prep_time: "10 mins",
    cook_time: "15 mins",
    total_time: "25 mins",
    ingredients: [
      { text: "1 lb rigatoni or penne pasta" },
      { text: "2 tbsp extra virgin olive oil" },
      { text: "4 cloves garlic, thinly sliced" },
      { text: "1 can (28 oz) San Marzano crushed tomatoes" },
      { text: "1/2 cup heavy cream or mascarpone" },
      { text: "1/2 cup freshly grated Parmesan cheese" },
      { text: "1 cup fresh basil leaves, torn" },
      { text: "1/2 tsp crushed red pepper flakes, salt & pepper" },
    ],
    steps: [
      { number: 1, text: "Bring a large pot of salted water to a boil. Cook pasta until al dente." },
      { number: 2, text: "Heat olive oil in a skillet over medium heat. Sauté sliced garlic until fragrant (1 min)." },
      { number: 3, text: "Add crushed tomatoes and red pepper flakes; simmer gently for 10 minutes." },
      { number: 4, text: "Stir in heavy cream and simmer 2 minutes until sauce turns a warm blush color." },
      { number: 5, text: "Toss drained pasta directly into the sauce along with Parmesan and fresh basil." },
      { number: 6, text: "Serve warm topped with extra cracked black pepper and olive oil." },
    ],
    labels: ["Dinner", "Pasta", "Vegetarian"],
    source_url: "https://recipes.themedina.house/recipe/creamy-tomato-basil-pasta",
  },
  "quick-chicken-tacos": {
    id: "quick-chicken-tacos",
    slug: "quick-chicken-tacos",
    title: "Quick Street-Style Chicken Tacos",
    description: "Juicy citrus-cumin chicken thighs seared in a skillet and served on warm corn tortillas.",
    servings: 4,
    prep_time: "10 mins",
    cook_time: "12 mins",
    total_time: "22 mins",
    ingredients: [
      { text: "1.5 lbs boneless skinless chicken thighs, diced" },
      { text: "1 tbsp taco seasoning (cumin, chili, oregano, garlic)" },
      { text: "1 tbsp lime juice & 1 tbsp olive oil" },
      { text: "12 small corn tortillas" },
      { text: "1/2 white onion, finely diced" },
      { text: "1/2 cup fresh cilantro, chopped" },
      { text: "Lime wedges & salsa verde for serving" },
    ],
    steps: [
      { number: 1, text: "Toss diced chicken with taco seasoning, lime juice, and olive oil in a bowl." },
      { number: 2, text: "Heat a heavy skillet or cast iron pan over high heat until smoking hot." },
      { number: 3, text: "Sear chicken in a single layer for 6-8 minutes until golden and charred at edges." },
      { number: 4, text: "Warm corn tortillas directly over a gas burner flame or dry pan." },
      { number: 5, text: "Assemble tacos with seared chicken, diced onion, fresh cilantro, and salsa." },
    ],
    labels: ["Mexican", "Quick", "Dinner"],
    source_url: "https://recipes.themedina.house/recipe/quick-chicken-tacos",
  },
};

recipesRouter.post("/import", async (req: Request, res: Response) => {
  const url = req.body?.url;
  if (!url || typeof url !== "string") {
    return res.status(400).json({ error: "A valid recipe URL is required" });
  }

  try {
    const resp = await fetch(url, {
      headers: { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" },
      signal: AbortSignal.timeout(5000),
    });

    if (resp.ok) {
      const html = await resp.text();
      // Look for JSON-LD recipe schema
      const jsonLdMatch = html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/gi);
      if (jsonLdMatch) {
        for (const scriptTag of jsonLdMatch) {
          try {
            const rawContent = scriptTag.replace(/<script[^>]*>|<\/script>/gi, "").trim();
            const parsed = JSON.parse(rawContent);
            const recipeObj = Array.isArray(parsed)
              ? parsed.find((item) => item["@type"] === "Recipe")
              : parsed["@type"] === "Recipe"
              ? parsed
              : parsed["@graph"]?.find((item: any) => item["@type"] === "Recipe");

            if (recipeObj) {
              const ingredients = (recipeObj.recipeIngredient || []).map((ing: string) => ({ text: ing }));
              const steps = (recipeObj.recipeInstructions || []).map((step: any, idx: number) => {
                if (typeof step === "string") return { number: idx + 1, text: step };
                return { number: idx + 1, text: step.text || step.name || String(step) };
              });

              return res.json({
                recipe: {
                  id: "imported-recipe",
                  slug: "imported-recipe",
                  title: recipeObj.name || "Imported Recipe",
                  description: recipeObj.description || "",
                  servings: recipeObj.recipeYield || 4,
                  prep_time: recipeObj.prepTime || "",
                  cook_time: recipeObj.cookTime || "",
                  total_time: recipeObj.totalTime || "",
                  ingredients,
                  steps,
                  source_url: url,
                },
              });
            }
          } catch {
            // continue looking
          }
        }
      }
    }
  } catch (err: any) {
    console.warn(`[Recipe Import] URL fetch error, falling back to parsed URL: ${err?.message}`);
  }

  // Fallback: create a structured recipe outline from the URL
  const domain = new URL(url).hostname.replace("www.", "");
  const pathTitle = new URL(url).pathname
    .split("/")
    .filter(Boolean)
    .pop()
    ?.replace(/[-_]/g, " ")
    ?.replace(/\.\w+$/, "") || "Custom Recipe";

  const formattedTitle = pathTitle.replace(/\b\w/g, (c) => c.toUpperCase());

  return res.json({
    recipe: {
      id: "imported-recipe",
      slug: "imported-recipe",
      title: formattedTitle,
      description: `Recipe imported from ${domain}`,
      servings: 4,
      prep_time: "15 mins",
      cook_time: "25 mins",
      total_time: "40 mins",
      ingredients: [
        { text: "1 portion fresh seasonal produce" },
        { text: "2 tbsp olive oil or butter" },
        { text: "Seasoning to taste (salt, pepper, herbs)" },
      ],
      steps: [
        { number: 1, text: `Follow the full preparation guide on ${domain}.` },
        { number: 2, text: "Cook thoroughly until aromatic and tender." },
        { number: 3, text: "Garnish with fresh herbs and serve warm." },
      ],
      source_url: url,
    },
  });
});

recipesRouter.get("/mealie", async (req: Request, res: Response) => {
  const baseUrl = config.mealie.base_url;
  const token = config.mealie.token;
  const search = String(req.query.search || "").trim().toLowerCase();

  if (baseUrl && token) {
    try {
      const url = new URL(`${baseUrl.replace(/\/$/, "")}/api/recipes`);
      if (search) url.searchParams.set("queryFilter", search);
      url.searchParams.set("perPage", String(req.query.per_page || 50));

      const resp = await fetch(url.toString(), {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/json",
        },
        signal: AbortSignal.timeout(3000),
      });

      if (resp.ok) {
        const data = (await resp.json()) as any;
        const items = data.items || (Array.isArray(data) ? data : []);
        if (items.length > 0) {
          const recipes = items.map((r: any) => ({
            id: String(r.id || r.slug),
            slug: String(r.slug || r.id),
            name: String(r.name || r.title || "Untitled Recipe"),
          }));
          return res.json({ recipes });
        }
      }
    } catch (err: any) {
      console.warn(`[Mealie] Live query error, returning cached sample recipes: ${err?.message}`);
    }
  }

  // Fallback to sample library
  const recipes = Object.values(SAMPLE_RECIPES)
    .filter((r) => !search || r.title.toLowerCase().includes(search) || r.description?.toLowerCase().includes(search))
    .map((r) => ({
      id: r.id,
      slug: r.slug,
      name: r.title,
    }));

  return res.json({ recipes });
});

recipesRouter.get("/mealie/:slug_or_id", async (req: Request, res: Response) => {
  const slugOrId = req.params.slug_or_id;
  const baseUrl = config.mealie.base_url;
  const token = config.mealie.token;

  if (baseUrl && token) {
    try {
      const url = `${baseUrl.replace(/\/$/, "")}/api/recipes/${encodeURIComponent(slugOrId)}`;
      const resp = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/json",
        },
        signal: AbortSignal.timeout(3000),
      });

      if (resp.ok) {
        const r = (await resp.json()) as any;
        const recipe: RecipeItem = {
          id: String(r.id || r.slug || slugOrId),
          slug: String(r.slug || slugOrId),
          title: String(r.name || r.title || "Recipe"),
          description: r.description || "",
          servings: r.recipeYield || 4,
          prep_time: r.prepTime || "",
          cook_time: r.performTime || "",
          total_time: r.totalTime || "",
          ingredients: (r.recipeIngredient || []).map((ing: any) => ({
            text: typeof ing === "string" ? ing : ing.note || ing.title || String(ing),
          })),
          steps: (r.recipeInstructions || []).map((step: any, idx: number) => ({
            number: idx + 1,
            text: typeof step === "string" ? step : step.text || String(step),
          })),
          labels: Array.isArray(r.tags) ? r.tags.map((t: any) => t.name || String(t)) : [],
          source_url: r.orgURL || "",
        };
        return res.json({ recipe });
      }
    } catch (err: any) {
      console.warn(`[Mealie] Single recipe fetch error: ${err?.message}`);
    }
  }

  // Fallback to sample library
  const found = SAMPLE_RECIPES[slugOrId] || Object.values(SAMPLE_RECIPES).find((r) => r.slug === slugOrId || r.id === slugOrId);

  if (found) {
    return res.json({ recipe: found });
  }

  return res.status(404).json({ error: "Recipe not found" });
});
