#!/usr/bin/env bash
# Renders the books (all, or the profiles given) and collects the PDFs in out/
# under the names TxSuite ships them as: "Trionic 5.pdf", "T5_manual.pdf", ...
set -euo pipefail
cd "$(dirname "$0")/.."
quarto=${QUARTO:-quarto}
profiles=("$@")
[ ${#profiles[@]} -gt 0 ] || profiles=(t5 t7 t8 t5-manual t7-manual t8-manual)
mkdir -p out
for p in "${profiles[@]}"; do
  "$quarto" render --profile "$p"
  for f in _book/"$p"/*.pdf; do
    name=$(basename "$f")
    cp "$f" "out/${name/Trionic-/Trionic }"   # Quarto turns the space into a dash
  done
done
ls -l out
