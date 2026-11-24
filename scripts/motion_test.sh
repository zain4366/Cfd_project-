#!/bin/bash
# Phase 1 check: move the overset mesh through one full flapping cycle (no flow solved) and record the hole cutting.
#   scripts/motion_test.sh <case dir> <figure dir> [steps per cycle]
set -eo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
CASE=$(realpath "$1"); OUT=$(realpath -m "$2"); NSTEP=${3:-200}
source "$ROOT/scripts/openfoam_env.sh"; source "$ROOT/scripts/run.sh"
cd "$CASE"
T=$(python3 -c "import sys; sys.path.insert(0,'$ROOT/scripts'); import params as P; print(P.PERIOD)")
DT=$(python3 -c "print($T/$NSTEP)")
foamDictionary system/controlDict -entry endTime -set "$T" > /dev/null
foamDictionary system/controlDict -entry deltaT -set "$DT" > /dev/null
foamDictionary system/controlDict -entry writeInterval -set $((NSTEP/8)) > /dev/null
SECONDS=0
runlog moveDynamicMesh moveDynamicMesh
echo "moveDynamicMesh: $NSTEP steps in $SECONDS s" | tee "$OUT/motion_timing.txt"
runlog writeCellCentres postProcess -func writeCellCentres
runlog writeCellVolumes postProcess -func writeCellVolumes || true
cp log.moveDynamicMesh log.writeCellCentres "$OUT/"
grep -i "orphan" log.moveDynamicMesh | sort | uniq -c > "$OUT/orphans.txt" || echo "no line mentioning orphans in the log" > "$OUT/orphans.txt"
grep -iE "overset|hole|interpolated" log.moveDynamicMesh | head -60 > "$OUT/overset_lines.txt" || true
python3 "$ROOT/scripts/plot_holecut.py" "$CASE" "$OUT"
