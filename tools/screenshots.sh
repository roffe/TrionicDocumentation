#!/usr/bin/env bash
# Refreshes the TxSuite pictures from a TuningSuites checkout:
#   books:   tN/images/txsuite/*.png, rendered by TNAppTest's BookScreenshots test
#   manuals: txsuite/images/<ecu>/*.png, copied from TuningSuites' docs/screenshots
#            (run docs/screenshots/generate.sh there first when TxSuite's look changed)
# tools/screenshots.sh ~/devel/TuningSuites [t5 t7 t8]
set -euo pipefail
docs=$(cd "$(dirname "$0")/.." && pwd)
ts=$(cd "${1:?usage: tools/screenshots.sh <TuningSuites checkout> [t5 t7 t8]}" && pwd)
shift
ecus=("$@")
[ ${#ecus[@]} -gt 0 ] || ecus=(t5 t7 t8)
for e in "${ecus[@]}"; do
  n=${e#t}
  (cd "$ts" && env "T${n}APP_BOOK_DUMP=$docs/$e/images/txsuite" \
    dotnet test "T${n}AppTest" -c Release --filter "FullyQualifiedName~BookScreenshots")
  for f in "$docs/txsuite/images/$e"/*.png; do
    cp "$ts/docs/screenshots/$e/$(basename "$f")" "$f"
  done
done
