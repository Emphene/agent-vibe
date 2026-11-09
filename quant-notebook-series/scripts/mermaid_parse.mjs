// Parse every diagram recorded by common/diagrams.py (JSON lines) with the real Mermaid parser.
// usage: node mermaid_parse.mjs <dump.jsonl>      exit code 1 if any diagram fails to parse.
import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";

const dom = new JSDOM("<!DOCTYPE html><body></body>", { pretendToBeVisual: true });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
Object.defineProperty(globalThis, "navigator", { value: dom.window.navigator, configurable: true });
// Mermaid sanitises labels (e.g. <br/>) with DOMPurify, which needs these DOM globals.
for (const name of ["Element", "HTMLElement", "Node", "NodeFilter", "DOMParser", "DocumentFragment",
                    "HTMLTemplateElement", "Text", "Comment", "MutationObserver"]) {
  if (!(name in globalThis)) globalThis[name] = dom.window[name];
}

const mermaid = (await import("mermaid")).default;
mermaid.initialize({ startOnLoad: false });

const lines = readFileSync(process.argv[2], "utf8").split("\n").filter(Boolean);
let failures = 0;
for (const [i, line] of lines.entries()) {
  const { source, caption } = JSON.parse(line);
  const label = `diagram ${i + 1} (${source.split("\n")[0].trim()})`;
  try {
    await mermaid.parse(source);
    console.log(`  ok    ${label}${caption ? "" : "  [no caption]"}`);
  } catch (e) {
    failures += 1;
    console.log(`  FAIL  ${label}\n        ${String(e.message || e).split("\n").slice(0, 3).join("\n        ")}`);
  }
}
console.log(`${lines.length - failures}/${lines.length} diagrams parsed`);
process.exit(failures ? 1 : 0);
