import re
import csv


def get_fields(syscall):
    syscall = syscall.replace("\n", "")
    res = syscall.split(" ")
    return res[0], res[1], res[-1]


def parse_call(syscall, fn_name):
    pid, timestamp, duration = get_fields(syscall)
    fn_args_list = get_fn_arguments(syscall, fn_name)
    return [pid, timestamp, duration] + fn_args_list


def get_fn_arguments(syscall, fn_name):
    pattern = re.compile("(?<=" + fn_name + "\().*(?=\))")
    fn_args_str = pattern.findall(syscall)[0]
    fn_args_list = [i.strip() for i in fn_args_str.split(",")]
    return fn_args_list


if __name__ == "__main__":
    strace_file = open("strace.txt", "r")

    syscall_to_args_map = {
        "mmap": ["addr", "length", "prot", "flags", "fd", "offset"],
    }

    metadata_headers = ["pid", "timestamp", "duration"]
    syscall_to_args_map = {key: metadata_headers + syscall_to_args_map[key] for key in syscall_to_args_map}
    syscall_results_map = {key: [] for key in syscall_to_args_map}

    for line in strace_file.readlines():
        for call_to_parse in syscall_to_args_map:
            if " " + call_to_parse + "(" in line:
                syscall_results_map[call_to_parse].append(parse_call(line, call_to_parse))
                break

    # Save results of each call in their own csv
    for call_name in syscall_to_args_map:
        print("Saving results/", call_name + ".csv")
        call_results_file = open("results/" + call_name + ".csv", "w")
        mmap_csv = csv.writer(call_results_file)
        mmap_csv.writerows(syscall_results_map[call_name])
        call_results_file.close()
    print("Done")

