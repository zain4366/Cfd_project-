#!/bin/bash
# Run the case's solver (controlDict "application") on 4 cores with a wall-clock limit, publishing progress every 15 min.
#   scripts/run_solver.sh <case dir> <output dir> <wall limit in minutes> <ci-results path>
set -eo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
CASE=$(realpath "$1"); OUT=$(realpath -m "$2"); LIMIT=${3:-300}; DEST=${4:-phase2/run}
source "$ROOT/scripts/openfoam_env.sh"
mkdir -p "$OUT/progress"; cd "$CASE"
progress() {
  while sleep 900; do
    python3 "$ROOT/scripts/post_forces.py" "$CASE" "$OUT/progress" --log log.solver > /dev/null 2>&1 || true
    tail -60 log.solver > "$OUT/progress/log_tail.txt" 2>/dev/null || true
    [ -n "$GITHUB_TOKEN" ] && bash "$ROOT/scripts/publish_results.sh" "$OUT/progress" "$DEST/progress" "progress $DEST" > /dev/null 2>&1 || true
  done
}
APP=$(foamDictionary -entry application -value system/controlDict)
progress > /dev/null 2>&1 & PPID_LOOP=$!     # no shared stdout: a sleeping loop must not hold the step's pipe open
SECONDS=0
set +e
# SIGUSR2 = OpenFOAM writes the current time and stops cleanly (controlDict: stopAtWriteNowSignal 12)
timeout -s USR2 --kill-after=15m ${LIMIT}m mpirun -np 4 --oversubscribe $APP -parallel > log.solver 2>&1
RC=$?
set -e
pkill -P $PPID_LOOP 2>/dev/null || true; kill $PPID_LOOP 2>/dev/null || true
echo "solver exit code $RC after $SECONDS s" | tee "$OUT/solver_exit.txt"
grep -q "^End" log.solver && echo "reached endTime" | tee -a "$OUT/solver_exit.txt" || echo "stopped before endTime" | tee -a "$OUT/solver_exit.txt"
