#!/usr/bin/env bash

echo "Generating plot for $1 to $2"

python3 generate_plot.py -i "$1" -o "$2"
