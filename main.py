import re
import csv
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd


def get_fields(syscall):
    syscall = syscall.replace("\n", "")
    res = syscall.split(" ")
    return res[0], res[1], res[-2], res[-1]


def parse_call(syscall, fn_name):
    pid, timestamp, ret_val, duration = get_fields(syscall)
    fn_args_list = get_fn_arguments(syscall, fn_name)
    return [pid, timestamp, ret_val, duration] + fn_args_list


def get_fn_arguments(syscall, fn_name):
    pattern = re.compile("(?<=" + fn_name + "\().*(?=\))")
    fn_args_str = pattern.findall(syscall)[0]
    fn_args_list = [i.strip() for i in fn_args_str.split(",")]
    return fn_args_list


def get_fields_for_unfinished(syscall):
    syscall = syscall.replace("\n", "")
    res = syscall.split(" ")
    return res[0], res[1]


def parse_call_for_unfinished(syscall, fn_name):
    pid, timestamp = get_fields_for_unfinished(syscall)
    fn_args_list = get_fn_arguments_for_unfinished(syscall, fn_name)
    return [pid, timestamp] + fn_args_list


def get_fn_arguments_for_unfinished(syscall, fn_name):
    pattern = re.compile("(?<=" + fn_name + "\().*(?=\<)")
    fn_args_str = pattern.findall(syscall)[0]
    fn_args_list = [i.strip() for i in fn_args_str.split(",")]
    return fn_args_list


def get_fields_for_resumed(syscall):
    syscall = syscall.replace("\n", "")
    res = syscall.split(" ")
    return res[0], res[-2], res[-1]


def draw_line_chart_mem_use():
    mmap_file = open('results/mmap.csv')
    munmap_file = open('results/munmap.csv')

    mmap_reader = csv.reader(mmap_file)
    munmap_reader = csv.reader(munmap_file)
    next(mmap_reader)
    next(munmap_reader)

    merged_values = []
    for row in mmap_reader:
        merged_values.append([datetime.strptime(str(row[1]), '%H:%M:%S.%f'), int(row[5])])
    for row in munmap_reader:
        merged_values.append([datetime.strptime(str(row[1]), '%H:%M:%S.%f'), -int(row[5])])

    merged_values.sort(key=lambda x: x[0])
    for i in range(1, len(merged_values)):
        merged_values[i][1] += merged_values[i - 1][1]

    plt.plot([x[0] for x in merged_values], [x[1] for x in merged_values])
    plt.gcf().autofmt_xdate()
    plt.title('mmap lengths - munmap lengths')

    plt.show()


if __name__ == "__main__":
    strace_file = open("strace2.txt", "r")

    syscall_to_args_map = {
        "mmap": ["addr", "length", "prot", "flags", "fd", "offset"],
        "mmap_anon": ["addr", "length", "prot", "flags", "fd", "offset"],
        "munmap": ["addr", "length"],
        "mprotect": ["addr", "length", "prot"],
        "brk": ["addr"],
        "shmdt": ["shmaddr"],
        "shmat": ["shmid", "shmaddr", "shmflg"],
    }

    metadata_headers = ["pid", "timestamp", "ret_val", "duration"]
    syscall_to_args_map = {key: metadata_headers + syscall_to_args_map[key] for key in syscall_to_args_map}
    syscall_results_map = {key: [syscall_to_args_map[key]] for key in syscall_to_args_map}
    syscall_to_stacks_map = dict()

    for line in strace_file.readlines():
        for call_to_parse in syscall_to_args_map:
            if " " + call_to_parse + "(" in line:
                if "<unfinished ...>" not in line:
                    arguments = parse_call(line, call_to_parse)    
                    syscall_results_map[call_to_parse].append(arguments)
                    if call_to_parse == "mmap" and ("MAP_ANON" in arguments[7] or "MAP_ANONYMOUS" in arguments[7]):
                        syscall_results_map["mmap_anon"].append(arguments)
                else:
                    arguments = parse_call_for_unfinished(line, call_to_parse)
                    if arguments[0] + call_to_parse not in syscall_to_stacks_map:
                        syscall_to_stacks_map[arguments[0] + call_to_parse] = []
                    syscall_to_stacks_map[arguments[0] + call_to_parse].append(arguments)
                break
            elif "<... " + call_to_parse + " resumed>" in line:
                fields = get_fields_for_resumed(line)
                arguments = syscall_to_stacks_map[fields[0] + call_to_parse].pop()
                arguments.insert(2, fields[-2])
                arguments.insert(3, fields[-1])
                syscall_results_map[call_to_parse].append(arguments)
                if call_to_parse == "mmap" and ("MAP_ANON" in arguments[7] or "MAP_ANONYMOUS" in arguments[7]):
                        syscall_results_map["mmap_anon"].append(arguments)
                break

    # Save results of each call in their own csv
    for call_name in syscall_to_args_map:
        print("Saving results/", call_name + ".csv")
        call_results_file = open("results/" + call_name + ".csv", "w")
        mmap_csv = csv.writer(call_results_file)
        mmap_csv.writerows(syscall_results_map[call_name])
        call_results_file.close()

    draw_line_chart_mem_use()
    print("Done")
