#!/usr/bin/env bash

REPORT_FILE=report

echo running "${@:1}"

perf mem record -a --type=load --data-page-size --code-page-size \
                --freq=79750 --strict-freq --timestamp --sample-cpu \
                --phys-data -- "${@:1}"


perf mem report --demangle-kernel --phys-data \
                --fields=+pid,cpu,time,data_page_size,code_page_size \
                --comms=gimp --field-separator=',' --pretty=raw --stdio > "${REPORT_FILE}.csv"


python3 clean_spaces.csv -i report.csv -o "${REPORT_FILE}_cleaned.csv"

python3 filter_csv.py -i "${REPORT_FILE}_cleaned.csv" -o "${REPORT_FILE}_filtered.csv"