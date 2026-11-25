#!/bin/bash
# After a run: reconstruct the latest time, compute vorticity, make the force tables and pictures.
#   scripts/finish_run.sh <case dir> <output dir>
set -eo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
CASE=$(realpath "$1"); OUT=$(realpath -m "$2")
source "$ROOT/scripts/openfoam_env.sh"; source "$ROOT/scripts/run.sh"
mkdir -p "$OUT"; cd "$CASE"
python3 "$ROOT/scripts/post_forces.py" "$CASE" "$OUT" --log log.solver || true
runlog reconstructPar reconstructPar -latestTime || true
runlog vorticity postProcess -func vorticity -latestTime || true
runlog cellCentres postProcess -func writeCellCentres -latestTime || true
python3 "$ROOT/scripts/plot_vorticity.py" "$CASE" "$OUT/vorticity_latest.png" || echo "vorticity plot failed"
grep -E "Courant Number|deltaT|^Time =|ExecutionTime" log.solver | tail -40 > "$OUT/log_tail.txt" || true
head -120 log.solver > "$OUT/log_head.txt"
grep -iE "warning|error|nan|orphan" log.solver | sort | uniq -c | sort -rn | head -30 > "$OUT/log_warnings.txt" || true
gzip -c log.solver > "$OUT/log.solver.gz"
cp system/controlDict system/fvSchemes system/fvSolution constant/dynamicMeshDict "$OUT/"
