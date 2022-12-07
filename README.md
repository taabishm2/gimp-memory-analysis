# Linux-Memory-Managment Profiling Tools
Includes various scripts that rely on strace, proc files, Valgrind, and perf to profile memory access patterns of an application

## Strace
* For each call to be parsed, add the call-name to args mapping in `syscall_to_args_map`
* Parser works for call with a format similar to `sudo strace -T -tt -o strace.txt -q -e trace=memory -fp 25787`
* Generates CSV per call in the `results` directory

## GIMP Test Usage

* Run `./bench.sh <test-name>` where test-name is one of the options below - 
1. unsharp-mask
2. resize
3. rotate
4. auto-levels

* Credits to Phoronix Test Suite 
