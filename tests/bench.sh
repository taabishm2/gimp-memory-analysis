case "$1" in
"unsharp-mask")
	gimp -i -b '(batch-unsharp-mask "*.JPG" 15.0 0.6 0)' -b '(gimp-quit 0)' &
	PID=$!
    ;;
"resize")
	gimp -i -b '(batch-resize-image "*.JPG" 600 400)' -b '(gimp-quit 0)' &
	PID=$!
    ;;
"rotate")
	gimp -i -b '(batch-rotate "*.JPG")' -b '(gimp-quit 0)' &
	PID=$!
    ;;
"auto-levels")
	gimp -i -b '(batch-auto-levels "*.JPG")' -b '(gimp-quit 0)' &
	PID=$!
    ;;
*)
	echo 2 > ~/test-exit-status
	exit
   ;;
esac

perf mem record -a --type=load --data-page-size --freq=79750 --strict-freq --phys-data --timestamp --sample-cpu --pid=$PID &
strace -T -tt -o strace.txt -q -e trace=memory -fp $PID
