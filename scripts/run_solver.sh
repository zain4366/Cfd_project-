#!/bin/bash
# Run overPimpleDyMFoam on 4 cores with a wall-clock limit, publishing progress every 15 min.
#   scripts/run_solver.sh <case dir> <output dir> <wall limit in minutes> <ci-results path>
set -eo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
CASE=$(realpath "$1"); OUT=$(realpath -m "$2"); LIMIT=${3:-300}; DEST=${4:-phase2/run}
source "$ROOT/scripts/openfoam_env.sh"
mkdir -p "$OUT/progress"; cd "$CASE"
progress() {
  while sleep 900; do
    python3 "$ROOT/scripts/post_forces.py" "$CASE" "$OUT/progress" --log log.overPimpleDyMFoam > /dev/null 2>&1 || true
    tail -60 log.overPimpleDyMFoam > "$OUT/progress/log_tail.txt" 2>/dev/null || true
    [ -n "$GITHUB_TOKEN" ] && bash "$ROOT/scripts/publish_results.sh" "$OUT/progress" "$DEST/progress" "progress $DEST" > /dev/null 2>&1 || true
  done
}
progress & PPID_LOOP=$!
SECONDS=0
set +e
# SIGUSR2 = OpenFOAM writes the current time and stops cleanly (controlDict: stopAtWriteNowSignal 12)
timeout -s USR2 --kill-after=15m ${LIMIT}m mpirun -np 4 --oversubscribe overPimpleDyMFoam -parallel > log.overPimpleDyMFoam 2>&1
RC=$?
set -e
kill $PPID_LOOP 2>/dev/null || true
echo "solver exit code $RC after $SECONDS s" | tee "$OUT/solver_exit.txt"
grep -q "^End" log.overPimpleDyMFoam && echo "reached endTime" | tee -a "$OUT/solver_exit.txt" || echo "stopped before endTime" | tee -a "$OUT/solver_exit.txt"
