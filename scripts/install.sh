#!/bin/bash
# Installs the ESI OpenFOAM release (overset lives only in the openfoam.com line) and the gmsh Python API.
# Every network step is retried (package servers occasionally fail for a few minutes).
set -eo pipefail
OF_VERSION=${OF_VERSION:-2412}
retry() { for i in 1 2 3 4 5 6; do "$@" && return 0; echo "attempt $i failed: $*"; sleep $((i * 30)); done; return 1; }
# third-party repositories preinstalled on the runner (e.g. packages.microsoft.com) sometimes refuse connections and
# break apt-get update; none of them is needed here
sudo rm -f /etc/apt/sources.list.d/microsoft*.list /etc/apt/sources.list.d/microsoft*.sources 2>/dev/null || true
retry bash -c "curl -fsS https://dl.openfoam.com/add-debian-repo.sh | sudo bash"
retry sudo apt-get update -qq
apt-cache search '^openfoam2[0-9]*-default' | sort || true
retry sudo apt-get install -y -qq openfoam${OF_VERSION}-default
# runtime libraries the gmsh wheel needs on a headless runner
retry sudo apt-get install -y -qq libglu1-mesa libxcursor1 libxinerama1 libxft2 libxrender1 libxi6
retry python3 -m pip install --quiet gmsh numpy matplotlib
