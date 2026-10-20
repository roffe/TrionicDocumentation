# Trionic Documentation

Dilemma's Trionic 5, 7 and 8 documentation and the TxSuite user manuals (once the T5Suite, T7Suite and T8Suite manuals), moved out of Word and into Markdown so everyone can help keep them up to date.

| Book | PDF |
|---|---|
| Analyzing Trionic 5 with TxSuite | `Trionic 5.pdf` |
| Analyzing Trionic 7 with TxSuite | `Trionic 7.pdf` |
| Analyzing Trionic 8 with TxSuite | `Trionic 8.pdf` |
| TxSuite user manual, Trionic 5 | `T5_manual.pdf` |
| TxSuite user manual, Trionic 7 | `T7_manual.pdf` |
| TxSuite user manual, Trionic 8 | `T8_manual.pdf` |

Every [release](../../releases) has the PDFs, and every push and PR builds them as artifacts too. They are the files TxSuite opens from its Help menu.

## Building

You need [Quarto](https://quarto.org/docs/get-started/) 1.10 or newer.

```sh
quarto render --profile t7     # one book, ends up in _book/t7/
tools/build.sh                 # all of them, collected in out/
```

## Helping out

Found something wrong or know something that's missing? Open an issue or send a PR, [CONTRIBUTING.md](CONTRIBUTING.md) has the how.

The books were converted from the original PDFs with `tools/pdf2qmd.py`, a one-off that isn't needed for anything anymore but stays here in case someone wonders where the files came from.
