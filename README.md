# strace-parser
* For each call to be parsed, add the call-name to args mapping in `syscall_to_args_map`
* Parser works for call with a format similar to `sudo strace -T -tt -o strace.txt -q -e trace=memory -fp 25787`
* Generates CSV per call in the `results` directory
