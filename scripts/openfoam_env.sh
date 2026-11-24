# source this: loads the pinned ESI OpenFOAM environment without tripping `set -e`
OF_VERSION=${OF_VERSION:-2412}
set +eu
source /usr/lib/openfoam/openfoam${OF_VERSION}/etc/bashrc
set -eo pipefail
