import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

/**
 * Vite añade crossorigin a <script type="module">; con file:// el bundle puede no
 * ejecutarse y la app sale en blanco. El reporte ETI se abre a menudo como archivo local.
 */
function stripCrossoriginForLocalHtml(): Plugin {
  return {
    name: "ungraph-strip-crossorigin",
    apply: "build",
    transformIndexHtml(html) {
      return html.replace(/\s+crossorigin(?:=[^\s>]*)?/gi, "");
    },
  };
}

export default defineConfig({
  plugins: [react(), stripCrossoriginForLocalHtml()],
  base: "./",
  build: {
    outDir: path.resolve(__dirname, "../ungraph/report_static"),
    emptyOutDir: true,
  },
});