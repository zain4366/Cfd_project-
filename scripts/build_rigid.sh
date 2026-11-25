#!/bin/bash
# Build the rigid moving O-grid case:  scripts/build_rigid.sh <coarse|medium|fine> [run dir] [figure dir]
set -eo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
LEVEL=${1:-medium}; RUN=$(realpath -m "${2:-run/rigid_$LEVEL}"); OUT=$(realpath -m "${3:-out/rigid_$LEVEL}")
source "$ROOT/scripts/openfoam_env.sh"; source "$ROOT/scripts/run.sh"
rm -rf "$RUN"; mkdir -p "$OUT"; cp -r "$ROOT/case_rigid" "$RUN"; cd "$RUN"
python3 "$ROOT/scripts/make_mesh_inputs.py" --rigid --level "$LEVEL" --case . --comp foil.msh --figs "$OUT" | tee "$OUT/mesh_generation.json"
runlog gmshToFoam gmshToFoam foil.msh
runlog changeDictionary changeDictionary -constant
runlog checkMesh checkMesh -constant || true
rm -rf 0 && cp -r 0.orig 0
cp log.* "$OUT/"; cp constant/polyMesh/boundary "$OUT/boundary.txt"
