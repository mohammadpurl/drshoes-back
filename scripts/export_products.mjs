import { writeFileSync, mkdirSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";
import { createRequire } from "module";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..", "..");

// Load TS via tsx register
const require = createRequire(import.meta.url);

async function main() {
  const { register } = await import("tsx/esm/api");
  register();

  const { products, reviews } = await import(
    join(root, "data", "products.ts")
  );

  const outDir = join(__dirname, "..", "data");
  mkdirSync(outDir, { recursive: true });
  writeFileSync(
    join(outDir, "products.json"),
    JSON.stringify({ products, reviews }, null, 2),
    "utf-8"
  );
  console.log(`Exported ${products.length} products, ${reviews.length} reviews`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
