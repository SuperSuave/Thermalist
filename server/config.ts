import path from "path";

export interface AppConfig {
  port: number;
  timezone: string;
  raw_tcp: {
    host: string;
    port: number;
    font: string;
    width: number;
    cut: boolean;
    initialize: boolean;
    dry_run: boolean;
  };
  donetick: {
    base_url: string;
    token: string;
  };
  mealie: {
    base_url: string;
    token: string;
    timeout_seconds: number;
  };
}

export const config: AppConfig = {
  port: Number(process.env.PORT) || 3000,
  timezone: process.env.TIMEZONE || "America/Los_Angeles",
  raw_tcp: {
    host: process.env.RAW_TCP_HOST || "192.168.86.9",
    port: Number(process.env.RAW_TCP_PORT) || 9100,
    font: process.env.RAW_TCP_FONT || "A",
    width: Number(process.env.RAW_TCP_WIDTH) || 48,
    cut: process.env.RAW_TCP_CUT !== "false",
    initialize: process.env.RAW_TCP_INITIALIZE !== "false",
    dry_run: process.env.RAW_TCP_DRY_RUN === "true",
  },
  donetick: {
    base_url: process.env.DONETICK_BASE_URL || "https://donetick.themedina.house",
    token: process.env.DONETICK_TOKEN || "299c9b193b160f735aff0461edb8a8fd6443e9b0280fb319f406743104da1f5b",
  },
  mealie: {
    base_url: process.env.MEALIE_BASE_URL || "https://recipes.themedina.house",
    token: process.env.MEALIE_TOKEN || "",
    timeout_seconds: Number(process.env.MEALIE_TIMEOUT_SECONDS) || 10,
  },
};
