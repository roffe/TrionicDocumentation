# Contributing

Fixes and new info are very welcome. Small stuff can be edited right here on GitHub with the pencil icon, every PR gets the PDFs built so you can check how it looks.

## Building

Install [Quarto](https://quarto.org/docs/get-started/) 1.10 or newer, it brings Pandoc and Typst with it. Then from the repo root:

```sh
quarto render --profile t7
```

The PDF ends up in `_book/t7/`. The profiles are `t5`, `t7`, `t8` (the Trionic books) and `t5-manual`, `t7-manual`, `t8-manual` (the TxSuite user manuals).

## Layout

- `t5/`, `t7/`, `t8/`, `t5-manual/`, `t7-manual/`, `t8-manual/`: one folder per book, a `.qmd` file per chapter and the pictures in `images/`.
- `txsuite/`: the chapters all three TxSuite manuals share, and the TxSuite screenshots in `txsuite/images/<ecu>/`. A bit only one ECU has goes in a `::: {.content-visible when-profile="t7-manual"}` block.
- `shared/images/`: drawings used by more than one book (pinouts, circuits, timing diagrams), as SVG.
- `_quarto-<book>.yml`: the book's title, chapters in order and the footer text. A new chapter needs to be listed there.
- `_quarto.yml`: what all books share.
- `_extensions/trionic/`: the look (Typst template, fonts, icons). Same for all books.
- `index.qmd`: empty on purpose, Quarto books need one.

## Writing

The chapters are Markdown ([Quarto's flavour](https://quarto.org/docs/authoring/markdown-basics.html)). A few rules so the diffs stay readable and the books look the same:

One sentence per line. Paragraphs are separated by a blank line. That way a change to one sentence is a one line diff.

Headings are `#` (chapter), `##`, `###` and `####`. A heading gets the "advanced technical topic" or "references" icon from the old documents with a class:

```markdown
## Checksum {.advanced}
## How to read compressor maps {.references}
```

Pictures go in the book's `images/` folder. A picture with a caption gets an id so it's numbered, and you refer to it with `@` instead of typing "Image 4":

```markdown
![Symbol table in T7 firmware](images/p015-1.png){#fig-symbol-table width=60%}

As you can see in @fig-symbol-table the table starts with ...
```

`width` is how much of the text width it takes. Leave out the caption and id for pictures that don't need a number.

Drawings (pinouts, circuits, block and timing diagrams) are SVG, not screenshots of them, so they stay sharp at any zoom. Write the text as real `<text>` with `font-family="DejaVu Sans" font-stretch="condensed"`, that's the font the books bundle, and it stays searchable. Look at one in `shared/images/` before making a new one.

The TxSuite screenshots aren't made by hand: they come from the Screenshots tests in [TuningSuites](https://github.com/roffe/TuningSuites) (`docs/screenshots/generate.sh`). A new one is added there and its light version copied to `txsuite/images/<ecu>/`.

Tables are pipe tables, first row is the header:

```markdown
| ID   | Byte 0 | Byte 1 | Byte 2 |
|------|--------|--------|--------|
| 348h | 11     | 02     | STATUS |
```

A table caption goes on its own line under the table and needs an id, without one it silently disappears from the PDF:

```markdown
: Footer identifiers {#tbl-footer-ids}
```

Hex dumps, code and anything where the spacing matters go in a code block (three backticks). Formulas are LaTeX math, `$x$` inline or `$$ ... $$` on their own line. Links are written `<https://example.com>` or `[text](https://example.com)`.

`*`, `_`, `@`, `$`, `<` and `#` mean something in Markdown, put a `\` in front when you mean the character itself (`Ign\_map\_0!` is fine as `Ign_map_0!` though, an `_` inside a word is left alone).

## Pull requests

Keep a PR to one thing (a chapter, a fix, a new section). CI builds all PDFs on every PR and attaches them to the run, have a look at the pages you changed before asking for a review.
