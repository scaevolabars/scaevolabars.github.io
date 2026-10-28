import mermaid from "/vendor/mermaid/mermaid.esm.min.mjs";

const style = getComputedStyle(document.documentElement);
const token = (name) => style.getPropertyValue(name).trim();
// Smallest scale for a diagram, so labels stay at about 12 px; below it the pre scrolls, like code.
const MIN_SCALE = 0.75;

mermaid.initialize({
  startOnLoad: false,
  theme: "base",
  look: "classic",
  layout: "dagre", // the default would load the 1.6 MB ELK layout engine
  suppressErrorRendering: true, // a bad diagram keeps its source visible; the error goes to the console
  flowchart: { padding: 8 },
  themeVariables: {
    background: token("--paper"),
    primaryColor: token("--paper"),
    primaryBorderColor: token("--ink"),
    primaryTextColor: token("--ink"),
    secondaryColor: token("--code-bg"),
    tertiaryColor: token("--code-bg"),
    lineColor: token("--ink"),
    fontFamily: token("--serif"),
  },
});

// Measure labels in Literata, not in the fallback font.
await document.fonts.ready;

const blocks = [...document.querySelectorAll("pre.mermaid")];
const sources = new Map(blocks.map((pre) => [pre, pre.textContent]));

try {
  await mermaid.run({ nodes: blocks });
} catch (error) {
  console.error("Mermaid could not draw a diagram:", error?.message ?? error);
} finally {
  for (const [i, pre] of blocks.entries()) {
    const svg = pre.querySelector("svg");
    if (!svg) {
      // Mermaid empties a block it cannot draw: put the source back, with the code look.
      pre.textContent = sources.get(pre);
      pre.removeAttribute("data-processed");
      console.error(`Mermaid could not draw diagram ${i + 1} on this page; its source is shown instead.`);
      continue;
    }
    // Mermaid puts the natural width in the inline max-width. A diagram without one is left alone.
    const natural = svg.style.maxWidth.endsWith("px") ? parseFloat(svg.style.maxWidth) : NaN;
    if (Number.isFinite(natural)) svg.style.minWidth = `${MIN_SCALE * natural}px`;
  }
}
