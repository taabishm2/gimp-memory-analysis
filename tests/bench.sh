gimp -i -b '(batch-unsharp-mask "*.JPG" 15.0 0.6 0)' -b '(gimp-quit 0)' &
PID=$!

perf mem record -a --type=load --data-page-size --freq=79750 --strict-freq --timestamp --sample-cpu --pid=$PID &
strace -T -tt -o strace.txt -q -e trace=memory -fp $PID
