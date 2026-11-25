#!/bin/bash
# Turn a meshed case into a flow run:  scripts/setup_run.sh <case dir> <inverseDistance|trackingInverseDistance> <cycles> [steps per cycle] [maxCo]
set -eo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
CASE=$(realpath "$1"); METHOD=${2:-inverseDistance}; NCYC=${3:-2}; SPC=${4:-2000}; MAXCO=${5:-1.0}
source "$ROOT/scripts/openfoam_env.sh"
cd "$CASE"
rm -rf [1-9]* 0.[0-9]* postProcessing processor* log.moveDynamicMesh   # remove anything left by the motion test
rm -rf 0 && cp -r 0.orig 0 && setFields > log.setFields.run 2>&1
read T DT END WI < <(python3 -c "
import sys; sys.path.insert(0,'$ROOT/scripts'); import params as P
T=P.PERIOD; print(T, T/$SPC, $NCYC*T, T/4)")
python3 - "$T" "$DT" "$END" "$WI" "$MAXCO" <<'PY'
import sys, re
T, dt, end, wi, maxco = sys.argv[1:]
s = open("system/controlDict").read()
for k, v in (("endTime", end), ("deltaT", dt), ("writeInterval", wi), ("writeControl", "adjustableRunTime")):
    s = re.sub(rf"^{k}\s+[^;]*;", f"{k}    {v};", s, flags=re.M)
s += f"""
{"adjustTimeStep  no;           // fixed time step, as in Kinsey & Dumas" if maxco == "fixed" else f"adjustTimeStep  yes;\nmaxCo           {maxco};\nmaxDeltaT       {dt};"}

OptimisationSwitches
{{
    stopAtWriteNowSignal 12;  // SIGUSR2 = write the current time and stop (used before the 6-hour job limit)
}}

functions
{{
    forces
    {{
        type            forces;
        libs            (forces);
        writeControl    timeStep;
        writeInterval   1;
        patches         (foil);
        rho             rhoInf;
        rhoInf          1;
        CofR            (0 0 0);  // moment about the origin; post-processing moves it to the moving pivot
        log             false;
    }}
    courant
    {{
        type            CourantNo;
        libs            (fieldFunctionObjects);
        writeControl    writeTime;
    }}
}}
"""
open("system/controlDict", "w").write(s)
f = open("system/fvSchemes").read()
f = f.replace("ddtSchemes      { default Euler; }", "ddtSchemes      { default backward; }")
open("system/fvSchemes", "w").write(f)
PY
# overset method (tracking needs a search box covering the whole domain, one division in z)
python3 - "$METHOD" <<'PY'
import sys, re
m = sys.argv[1]
f = open("system/fvSchemes").read()
block = f"oversetInterpolation\n{{\n    method          {m};\n"
if m == "trackingInverseDistance":
    block += "    searchBox       (-6 -18 0) (18 18 0.1);\n    searchBoxDivisions ((400 600 1) (400 600 1));\n    allowInterpolatedDonors false;\n"
block += "}"
f = re.sub(r"oversetInterpolation\s*\{[^}]*\}", block, f)
open("system/fvSchemes", "w").write(f)
PY
[ "$MAXCO" = "fixed" ] && sed -i "s/nOuterCorrectors    1;/nOuterCorrectors    2;/" system/fvSolution
decomposePar -force > log.decomposePar 2>&1 || { tail -30 log.decomposePar; exit 1; }
grep -A6 "^oversetInterpolation" system/fvSchemes
grep -E "^(endTime|deltaT|maxCo|maxDeltaT|writeInterval)" system/controlDict
