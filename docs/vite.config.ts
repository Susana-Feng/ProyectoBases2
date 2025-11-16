import tailwindcss from "@tailwindcss/vite";
import { tanstackStart } from "@tanstack/react-start/plugin/vite";
import react from "@vitejs/plugin-react";
import mdx from "fumadocs-mdx/vite";
import { defineConfig } from "vite";
import tsConfigPaths from "vite-tsconfig-paths";
import { i18n } from "./src/lib/i18n";

export default defineConfig({
  server: {
    port: 3000,
  },
  plugins: [
    mdx(await import("./source.config")),
    tailwindcss(),
    tsConfigPaths({
      projects: ["./tsconfig.json"],
    }),
    tanstackStart({
      prerender: {
        enabled: true,
        filter: ({ path }) => {
          // Prerenderizar todas las rutas que empiecen con los idiomas configurados
          if (path === "/") return true;
          const langPrefix = path.split("/")[1];
          return (i18n.languages as readonly string[]).includes(langPrefix);
        },
      },
    }),
    react(),
  ],
});
