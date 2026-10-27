import mermaid from "/vendor/mermaid/mermaid.esm.min.mjs";

const style = getComputedStyle(document.documentElement);
const token = (name) => style.getPropertyValue(name).trim();

mermaid.initialize({
  startOnLoad: false,
  theme: "base",
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
