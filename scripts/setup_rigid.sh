#!/bin/bash
# scripts/setup_rigid.sh <case dir> <cycles> [steps per cycle]
# optional environment: GRADU="cellLimited Gauss linear 1" (velocity-gradient limiter), NOUTER=4 (PIMPLE outer loops)
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
[ -n "$NOUTER" ] && foamDictionary system/fvSolution -entry PIMPLE/nOuterCorrectors -set "$NOUTER" > /dev/null
grep -E "grad\(U\)|nOuterCorrectors" system/fvSchemes system/fvSolution || true
decomposePar -force > log.decomposePar 2>&1 || { tail -30 log.decomposePar; exit 1; }
grep -E "^(endTime|deltaT|writeInterval)" system/controlDict
