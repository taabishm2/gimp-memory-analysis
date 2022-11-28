#!/usr/bin/env bash

echo running "${@:1}"

perf mem record -a --type=load --data-page-size --code-page-size \
                --freq=79750 --strict-freq --timestamp --sample-cpu \
                --phys-data -- "${@:1}"
