#!/bin/bash
# Build the overset mesh for one level:  scripts/build_mesh.sh <coarse|medium|fine> [run dir] [figure dir]
set -eo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
LEVEL=${1:-medium}; RUN=$(realpath -m "${2:-run/$LEVEL}"); OUT=$(realpath -m "${3:-out/$LEVEL}")
source "$ROOT/scripts/openfoam_env.sh"; source "$ROOT/scripts/run.sh"
rm -rf "$RUN"; mkdir -p "$RUN/component/system" "$OUT"
cp -r "$ROOT/case" "$RUN/main"
cp "$ROOT/case/system/"{controlDict,fvSchemes,fvSolution} "$RUN/component/system/"
python3 "$ROOT/scripts/make_mesh_inputs.py" --level "$LEVEL" --case "$RUN/main" --comp "$RUN/component/foil.msh" --figs "$OUT" | tee "$OUT/mesh_generation.json"

cd "$RUN/component"                                   # ---- O-grid around the foil
runlog gmshToFoam gmshToFoam foil.msh
# gmsh gives every patch the type "patch". Set front/back to empty (2D) BEFORE merging: otherwise mergeMeshes keeps
# a separate "frontAndBack_component" patch, and overset hole cutting treats that ordinary patch like a wall,
# which floods the whole background with holes.
cp "$ROOT/case/system/changeDictionaryDict" system/
runlog changeDictionary.component changeDictionary -constant
runlog checkMesh checkMesh -constant || true
cd "$RUN/main"                                        # ---- background, then merge
runlog blockMesh blockMesh
runlog checkMesh.background checkMesh -constant || true
runlog mergeMeshes mergeMeshes . ../component -overwrite
runlog changeDictionary changeDictionary -constant
runlog topoSet topoSet -constant
rm -rf 0 && cp -r 0.orig 0
runlog setFields setFields
runlog checkMesh.merged checkMesh || true
cp "$RUN/component/log.gmshToFoam" "$RUN/component/log.checkMesh" "$RUN/component/log.changeDictionary.component" "$OUT/" 2>/dev/null || true
for f in log.*; do cp "$f" "$OUT/"; done
cp constant/polyMesh/boundary "$OUT/boundary.txt"
echo "mesh built in $RUN/main"
