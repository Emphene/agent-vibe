# Fetching Papers via AlphaXiv

Use alphaxiv.org to get structured, LLM-friendly paper content. This is faster and more reliable than trying to read a raw PDF.

## Extract the paper ID

Parse the paper ID from whatever the user provides:

| Input | Paper ID |
|-------|----------|
| `https://arxiv.org/abs/2401.12345` | `2401.12345` |
| `https://arxiv.org/pdf/2401.12345` | `2401.12345` |
| `https://alphaxiv.org/overview/2401.12345` | `2401.12345` |
| `2401.12345v2` | `2401.12345v2` |
| `2401.12345` | `2401.12345` |

## Fetch the AI-generated overview (try this first)

```bash
curl -sL "https://alphaxiv.org/overview/{PAPER_ID}.md"
```

Returns a structured, detailed analysis of the paper as plain markdown. One call, no JSON parsing.

## Fetch the full paper text (fallback)

If the overview doesn't contain the specific detail you need (e.g., a particular equation, table, or proof):

```bash
curl -sL "https://alphaxiv.org/abs/{PAPER_ID}.md"
```

Returns the full extracted text of the paper as markdown.

## Local PDF files (no Arxiv ID)

If the user supplies a PDF instead of a link — a file on disk, an attachment, or a non-Arxiv URL — skip alphaxiv entirely. Note that `pdftotext` reads files, not URLs, so download first if needed:

```bash
curl -sL -o paper.pdf "https://example.com/paper.pdf"
```

Then extract the text locally with `pdftotext` (poppler-utils).

```bash
pdfinfo paper.pdf                 # page count, title, author — cheap sanity check
pdftotext paper.pdf -             # write plain text to stdout
```

Use plain `pdftotext` with no layout flag. It already reads multi-column papers in correct column order, which is what you want for comprehension. **Do not pass `-layout`**: it preserves the original visual layout, which on a two-column paper interleaves both columns side by side and makes the text much harder to follow.

**Extract selectively.** A full paper can run past 50k characters, which crowds out the rest of the context. Target the parts you need instead of dumping everything:

```bash
pdftotext -f 3 -l 6 paper.pdf -   # pages 3-6 only
```

Page numbers from `pdfinfo` include front matter, so the abstract is rarely page 1. Read a couple of pages to calibrate before extracting a range.

**Equations come through badly.** `pdftotext` flattens math into approximate ASCII — subscripts, superscripts, and fractions are lost. Use the text to find which equation matters and what the surrounding prose claims about it, then write the LaTeX by hand for the notebook. Don't try to transcribe symbols verbatim.

Scanned or image-only PDFs yield no text. Check with `pdftotext paper.pdf - | wc -c` — a near-zero result means the PDF needs OCR, which isn't available here. Ask the user for a text-based version or an Arxiv link.

## Error handling

- **Always pass `-L`.** `alphaxiv.org` redirects to `www.alphaxiv.org`. Without `-L`, curl returns a `301 Moved Permanently` HTML page that will silently masquerade as paper content.
- **404 on the overview**: Report hasn't been generated for this paper yet. Try the full text instead.
- **404 on the full text**: Text hasn't been processed yet. Last resort: download the PDF with `curl -sL -o paper.pdf "https://arxiv.org/pdf/{PAPER_ID}"` and use the `pdftotext` path above.
- No authentication is required — these are public endpoints.
