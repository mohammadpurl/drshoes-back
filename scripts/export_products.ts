import { mkdirSync, writeFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";
import { products, reviews } from "../../data/products";

const __dirname = dirname(fileURLToPath(import.meta.url));
const outDir = join(__dirname, "..", "data");
mkdirSync(outDir, { recursive: true });
writeFileSync(
  join(outDir, "products.json"),
  JSON.stringify({ products, reviews }, null, 2),
  "utf-8"
);
console.log(`Exported ${products.length} products, ${reviews.length} reviews`);
