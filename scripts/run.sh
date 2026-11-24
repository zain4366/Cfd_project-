# helper: run an OpenFOAM utility, keep its log, stop with the log tail if it fails
runlog() { local name=$1; shift; echo ">> $name: $*"; if ! "$@" > "log.$name" 2>&1; then echo "FAILED: $name"; tail -40 "log.$name"; return 1; fi; }
