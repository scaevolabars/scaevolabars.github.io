# Personal site and blog: design

Date: 2026-10-27
Status: approved

## Goal

Replace the unmodified al-folio fork with a custom Hugo site for Sergey Bars:
a short profile plus a technical blog. The subject is an engineer's notebook
about markets, machines and models. Readers are engineers, quant peers and
recruiters. The main job is long technical posts with code, math and diagrams.

Topics: trading systems, low-latency C++/Rust, GPU/CUDA, algorithms, math,
physics, foundation models, robotics.

## Decisions

| Question | Choice | Reason |
|---|---|---|
| Purpose | Profile + tech blog | Blog is the main content |
| Base | Custom design | Distinct look, no theme dependency |
| Generator | Hugo 0.166.0, pinned in devbox | One binary, build-time math and highlighting |
| Look | Engineering computation pad | Fits all topics; sidenotes suit dense writing |

## 1. Structure and content

Navigation: Writing, Notes, Projects, CV, About.

```
content/
  _index.md     Home: 2-3 sentence intro, 5 latest posts, 3 latest notes
  posts/        Long posts. Front matter: title, date, topics, summary, draft
  notes/        Paper notes. Adds: paper, authors, year, url
  projects.md   Renders data/projects.yaml (name, year, text, links)
  cv.md         Renders data/cv.yaml; links static/cv.pdf if present
  about.md      Free Markdown
data/
  projects.yaml
  cv.yaml
```

URLs:

- `/posts/<slug>/`, `/notes/<slug>/` for single entries
- `/posts/` archive grouped by year; `/notes/` likewise
- `/topics/<topic>/` lists posts and notes for one topic
- `/index.xml` RSS for posts and notes

Topics are a fixed list of eight slugs: `trading`, `low-latency`, `gpu`,
`algorithms`, `math`, `physics`, `foundation-models`, `robotics`. The build
warns (and so fails, with `--panicOnWarning`) on an unknown topic.

All al-folio files, demo posts, and Ruby/Docker files are removed. Git history
stays. Bio, CV and projects ship as clearly marked placeholders. One draft
sample post exercises code, math, a sidenote and a diagram; drafts are not
published.

## 2. Visual system

Colors (dark variant follows `prefers-color-scheme`; no toggle):

| Role | Light | Dark |
|---|---|---|
| Paper | `#EEF2E9` | `#1C211E` |
| Grid | `#CFDACB` | `#2A322D` |
| Ink | `#22272B` | `#DDE4DA` |
| Muted ink | `#5B635D` | `#9AA59C` |
| Pencil (links, note marks) | `#2B5C8F` | `#93B8E0` |
| Code background | `#E3E9DF` | `#232A26` |

Type:

- Literata variable (optical size axis) for text and headings; body 18 px,
  line height 1.65.
- JetBrains Mono for code only.
- Tabular lining figures for dates and tables.
- Fonts are self-hosted woff2, subset to Latin, Latin Extended, Greek and
  Cyrillic.

Layout:

```
┌┬─┬─┬─┬─ 5 mm grid band ─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
│ Sergey Bars     Writing Notes Projects CV About│
└┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
    Title
    21 October 2026, in Trading

    Text column, 66 characters,  ┊ ¹ Sidenote,
    left-aligned.¹               ┊   15rem wide
```

- The grid band is the one bold element. On Home it is taller and holds the
  name and intro. Everything below is quiet.
- Lists are plain rows: date, title, topics. No cards, no thumbnails.
- Sidenotes: `{{% note %}}…{{% /note %}}` shortcode. At 1100 px and wider the
  note floats in the right margin. Narrower, the number is a CSS-only toggle
  that opens the note under the paragraph.
- Code: custom Chroma theme from the palette.
- Display math is centered; everything else is left-aligned.
- Motion: only the sidenote opening on tap.
- Quality floor: works at 360 px, visible focus, skip link, text contrast at
  least 4.5:1 in both schemes.

## 3. Rendering, build, deploy, checks

Rendering:

- Math: goldmark passthrough for `$…$` and `$$…$$`, rendered to KaTeX HTML at
  build time with `transform.ToMath`. Pages load KaTeX CSS only.
- Code: Chroma at build time with CSS classes.
- Diagrams: a `mermaid` code block render hook marks the page; only marked
  pages load a self-hosted Mermaid script.
- RSS and sitemap from Hugo.

Build and deploy:

```
devbox.json pins hugo@0.166.0
  devbox run dev     hugo server with drafts
  devbox run build   hugo --gc --minify --panicOnWarning

push to master → GitHub Actions → devbox install → devbox run build
              → upload-pages-artifact → deploy-pages
pull request   → build only
```

- Old workflows (Docker image, gh-pages push) are removed.
- Pages source changes from "branch master" to "GitHub Actions" with one
  `gh api` call, run only after the owner approves.
- The old `gh-pages` branch is left in place.

Checks before the work is called done:

1. `devbox run build` passes with no warnings.
2. A link check on `public/` finds no broken internal links.
3. A script checks every text/background color pair against 4.5:1.
4. Screenshots at 360, 768 and 1280 px, light and dark: home, archive, a post
   with sidenote + math + code + diagram, a note, CV, projects.

Work happens on branch `hugo-site`. The owner then chooses merge, PR, or keep.
