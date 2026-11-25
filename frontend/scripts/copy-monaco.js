const fs = require("fs");
const path = require("path");

const src = path.join(__dirname, "..", "node_modules", "monaco-editor", "min", "vs");
const dst = path.join(__dirname, "..", "public", "vs");

if (fs.existsSync(src)) {
  console.log("[copy-monaco] Copying Monaco assets from node_modules to public/vs...");
  fs.cpSync(src, dst, { recursive: true });

  // Strip sourcemap reference from loader.js to prevent browser 404 logs in production
  const loaderPath = path.join(dst, "loader.js");
  if (fs.existsSync(loaderPath)) {
    const content = fs.readFileSync(loaderPath, "utf8").replace(/\/\/# sourceMappingURL=.*$/m, "");
    fs.writeFileSync(loaderPath, content, "utf8");
  }
  console.log("[copy-monaco] Monaco assets successfully deployed to public/vs.");
} else {
  console.warn("[copy-monaco] Warning: monaco-editor node_modules not found. Run npm install first.");
}
