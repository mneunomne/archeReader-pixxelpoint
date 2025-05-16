#!/bin/bash

# Path to your conda installation
CONDA_BASE="$HOME/miniconda3"  # or ~/anaconda3, depending on your setup

# Source the conda.sh script to initialize conda in the shell
source "$CONDA_BASE/etc/profile.d/conda.sh"

# Activate the desired environment
conda activate arche

cd /Users/atol/archeReader-pixxelpoint
python app -f -k