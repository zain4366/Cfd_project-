#!/bin/bash
# Installs the ESI OpenFOAM release (overset lives only in the openfoam.com line) and the gmsh Python API.
set -eo pipefail
OF_VERSION=${OF_VERSION:-2412}
curl -s https://dl.openfoam.com/add-debian-repo.sh | sudo bash
sudo apt-get update -qq
apt-cache search '^openfoam2[0-9]*-default' | sort || true
sudo apt-get install -y -qq openfoam${OF_VERSION}-default
# runtime libraries the gmsh wheel needs on a headless runner
sudo apt-get install -y -qq libglu1-mesa libxcursor1 libxinerama1 libxft2 libxrender1 libxi6
python3 -m pip install --quiet gmsh numpy matplotlib
