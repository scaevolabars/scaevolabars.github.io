# scaevolabars.github.io

Personal site and blog of Sergey Bars. Built with Hugo, deployed to GitHub Pages.

## Setup

Install [devbox](https://www.jetify.com/devbox). It pins Hugo and uv.

## Write

```bash
devbox run -- hugo new content posts/my-post.md     # new post, starts as a draft
devbox run -- hugo new content notes/paper-name.md  # new paper note, starts as a draft
devbox run dev                                      # preview with drafts at http://localhost:1313
```

Set `draft: false` to publish. Drafts are not published, but the tests and CI build them: a draft that breaks the build or the tests stops the deploy. Topics must be slugs from `params.topics` in `hugo.toml`; any other topic fails the build. Raw HTML in Markdown also fails the build: put code such as `vector<T>` in backticks.

- Headings: start sections at `##`. The title is the page's only h1; the tests fail on a second one.
- Sidenote: `text{{< note >}}Note text.{{< /note >}} more text`
- Math: `$inline$` and `$$display$$`. Write `\$` for a literal dollar sign in text; inline math that starts or ends with a space fails the build, which catches prices such as `$5 and $10`. Inside a formula, write `\text{\textdollar}` for a dollar sign.
- Diagram: a fenced code block with the language `mermaid`.
- CV: `data/cv.yaml`. Projects: `data/projects.yaml`. For a PDF CV, put it in `static/` and set `pdf` in `data/cv.yaml`.
- Keep the drafts `content/posts/sample-features.md`, `content/posts/sample-older.md` and `content/notes/sample-note.md`. They are never published; the tests use them, and they show every feature in use.

## Check

```bash
devbox run test           # build the site and run the tests
devbox run check-content  # fails while "PLACEHOLDER:" text remains in the built site (it does not decode PDFs)
```

## Deploy

One-time setting: set Settings → Pages → Build and deployment → Source to GitHub Actions before the first merge to `master`.

Push to `master`. GitHub Actions tests, builds and deploys the site. The deploy stops while "PLACEHOLDER:" text remains. The check does not decode PDF files, so check a PDF CV by hand.

## Third-party files

- `scripts/vendor.sh` fetches KaTeX CSS and Mermaid (pinned versions, SHA-256 checked) into `static/vendor/`, which git ignores.
- `scripts/fonts.sh` rebuilds the font subsets in `static/fonts/`, which are committed. Literata and JetBrains Mono use the SIL Open Font License.
