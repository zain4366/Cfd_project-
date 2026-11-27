#!/bin/bash
# scripts/setup_rigid.sh <case dir> <cycles> [steps per cycle]
# optional environment (numerics tests): GRADU="cellLimited Gauss linear 1"  NOUTER=4  DDT=Euler
#   LAPL="limited corrected 0.33" (laplacian + snGrad)  DIVU="Gauss limitedLinearV 1"  STATIC=1 (mesh does not move)  POTENTIAL=1 (potentialFoam start)
set -eo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
CASE=$(realpath "$1"); NCYC=${2:-3}; SPC=${3:-2000}
source "$ROOT/scripts/openfoam_env.sh"; cd "$CASE"
read T DT END WI < <(python3 -c "
import sys; sys.path.insert(0,'$ROOT/scripts'); import params as P
T=P.PERIOD; print(T, T/$SPC, $NCYC*T, T/4)")
foamDictionary system/controlDict -entry endTime -set "$END" > /dev/null
foamDictionary system/controlDict -entry deltaT -set "$DT" > /dev/null
foamDictionary system/controlDict -entry writeInterval -set "$WI" > /dev/null
[ -n "$GRADU" ] && foamDictionary system/fvSchemes -entry "gradSchemes/grad(U)" -set "$GRADU" > /dev/null
[ -n "$DDT" ] && foamDictionary system/fvSchemes -entry ddtSchemes/default -set "$DDT" > /dev/null
[ -n "$DIVU" ] && foamDictionary system/fvSchemes -entry "divSchemes/div(phi,U)" -set "$DIVU" > /dev/null
[ -n "$LAPL" ] && foamDictionary system/fvSchemes -entry laplacianSchemes/default -set "Gauss linear $LAPL" > /dev/null
[ -n "$LAPL" ] && foamDictionary system/fvSchemes -entry snGradSchemes/default -set "$LAPL" > /dev/null
[ -n "$STATIC" ] && foamDictionary constant/dynamicMeshDict -entry dynamicFvMesh -set staticFvMesh > /dev/null
if [ -n "$POTENTIAL" ]; then        # smooth start: potential-flow initial field instead of U = 1 up to the wall
  foamDictionary system/fvSolution -entry potentialFlow -set "{ nNonOrthogonalCorrectors 3; }" > /dev/null
  foamDictionary system/fvSolution -entry solvers/Phi -set "{ solver GAMG; smoother GaussSeidel; tolerance 1e-7; relTol 0.01; }" > /dev/null
  foamDictionary system/fvSchemes -entry "divSchemes/div(div(phi,U))" -set "Gauss linear" > /dev/null
  potentialFoam -writep -writePhi > log.potentialFoam 2>&1 || { tail -30 log.potentialFoam; exit 1; }
  tail -4 log.potentialFoam
fi
[ -n "$NOUTER" ] && foamDictionary system/fvSolution -entry PIMPLE/nOuterCorrectors -set "$NOUTER" > /dev/null
grep -E "grad\(U\)|nOuterCorrectors|default|div\(phi,U\)" system/fvSchemes system/fvSolution || true
decomposePar -force > log.decomposePar 2>&1 || { tail -30 log.decomposePar; exit 1; }
grep -E "^(endTime|deltaT|writeInterval)" system/controlDict
