import mermaid from "/vendor/mermaid/mermaid.esm.min.mjs";

const style = getComputedStyle(document.documentElement);
const token = (name) => style.getPropertyValue(name).trim();
// Smallest scale for a diagram, so labels stay at about 12 px; below it the pre scrolls, like code.
const MIN_SCALE = 0.75;

mermaid.initialize({
  startOnLoad: false,
  theme: "base",
  look: "classic",
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

await mermaid.run({ querySelector: "pre.mermaid" });

// Mermaid puts the natural width in the inline max-width. A diagram without one is left alone.
for (const svg of document.querySelectorAll("pre.mermaid svg")) {
  const natural = svg.style.maxWidth.endsWith("px") ? parseFloat(svg.style.maxWidth) : NaN;
  if (Number.isFinite(natural)) svg.style.minWidth = `${MIN_SCALE * natural}px`;
}
