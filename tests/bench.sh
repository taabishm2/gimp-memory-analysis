cp bench.sh ~/.config/GIMP/*/scripts
files=`ls *.JPG | xargs`

case "$1" in
"unsharp-mask")
	BATCH_COMMAND="(batch-unsharp-mask \"$files\" 15.0 0.6 0)"
    ;;
"resize")
	BATCH_COMMAND="(batch-resize-image \"$files\" 600 400)"
    ;;
"rotate")
	BATCH_COMMAND="(batch-rotate \"$files\")"
    ;;
"auto-levels")
	BATCH_COMMAND="(batch-auto-levels \"$files\")"
    ;;
*)
	echo 2 > ~/test-exit-status
	exit
   ;;
esac

gimp -i -b \'$BATCH_COMMAND\' -b '(gimp-quit 0)'
