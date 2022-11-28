#!/usr/bin/env bash

echo "Saving report to $1"

perf mem report --demangle-kernel --phys-data \
                --fields=+pid,cpu,time,data_page_size,code_page_size \
                --comms=gimp --field-separator=',' --pretty=raw --stdio > "/tmp/report_raw.csv"


python3 clean_spaces.csv -i "/tmp/report_raw.csv" -o "/tmp/report_cleaned.csv"

python3 filter_csv.py -i "/tmp/report_cleaned.csv" -o "$1"
