#!/bin/bash
# scripts/setup_rigid.sh <case dir> <cycles> [steps per cycle]
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
decomposePar -force > log.decomposePar 2>&1 || { tail -30 log.decomposePar; exit 1; }
grep -E "^(endTime|deltaT|writeInterval)" system/controlDict
