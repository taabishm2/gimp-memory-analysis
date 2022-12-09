from collections import defaultdict
import matplotlib.pyplot as plt
from enum import Enum
import subprocess
import time
import csv
import os
import re
import math


class GraphName(Enum):
    PROC_MEMORY_CONSUMPTION = 1
    PROC_PAGE_FAULTS = 2
    STRACE_MEMORY_COUNT_HIST = 3
    STRACE_MEMORY_MEMORY_HIST = 4


class AllocatorName(Enum):
    LIB_C = 1
    TC_MALLOC = 2
    MI_MALLOC = 3
    TBB_MALLOC = 4
    JE_MALLOC = 5


class GimpTestName(Enum):
    UNSHARP = 1
    RESIZE = 2
    ROTATE = 3
    AUTO_LEVEL = 4


TEST_CMD_MAP = {
    GimpTestName.UNSHARP: """ gimp -i -b '(batch-unsharp-mask "*.JPG" 15.0 0.6 0)' -b '(gimp-quit 0)' """
}

ALLOCATOR_CMD_PREFIX_MAP = {
    AllocatorName.LIB_C: "",
    AllocatorName.TC_MALLOC: "",
    AllocatorName.MI_MALLOC: "",
    AllocatorName.TBB_MALLOC: "",
    AllocatorName.JE_MALLOC: ""
}


class Graph:

    def __init__(self, allocator: AllocatorName):
        self.allocator = allocator

    def plot(self):
        for gimp_test in GimpTestName:
            if gimp_test != GimpTestName.UNSHARP: continue

            print("# PLOTTING FAULTS FOR", gimp_test.name)
            plt.clf()
            self.plot_proc_page_faults(gimp_test)

            print("# PLOTTING MEMUSE FOR", gimp_test.name)
            plt.clf()
            self.plot_memory_consumed(gimp_test)

            print("# PLOTTING MEM-CNT FOR", gimp_test.name)
            plt.clf()
            self.plot_memory_memory_count(gimp_test)

            print("# PLOTTING MEM-MEM FOR", gimp_test.name)
            plt.clf()
            self.plot_memory_memory_size(gimp_test)

    def plot_memory_memory_size(self, gimp_test: GimpTestName):
        mmap_file = open("input/" + self.allocator.name + "-" + gimp_test.name + "-mmap-parsed.csv")
        munmap_file = open("input/" + self.allocator.name + "-" + gimp_test.name + "-munmap-parsed.csv")
        brk_file = open("input/" + self.allocator.name + "-" + gimp_test.name + "-brk-parsed.csv")

        mmap_reader = csv.reader(mmap_file)
        munmap_reader = csv.reader(munmap_file)
        brk_reader = csv.reader(brk_file)
        next(mmap_reader)
        next(munmap_reader)
        next(brk_reader)

        bins = 100
        mmap_sizes = [math.log(int(i[5])) for i in mmap_reader]
        hist = [0] * bins
        interval_size = math.ceil(max(mmap_sizes) / bins)
        for i in mmap_sizes:
            hist[int(i // interval_size)] += i

        plt.bar([i for i in range(bins)], hist)

        plt.ylabel('Memory')
        plt.xlabel('Log(Memory)')
        plt.savefig(
            "output/" + self.allocator.name + "-" + gimp_test.name + "-" + GraphName.STRACE_MEMORY_MEMORY_HIST.name)

    def plot_memory_memory_count(self, gimp_test: GimpTestName):
        mmap_file = open("input/" + self.allocator.name + "-" + gimp_test.name + "-mmap-parsed.csv")
        munmap_file = open("input/" + self.allocator.name + "-" + gimp_test.name + "-munmap-parsed.csv")
        brk_file = open("input/" + self.allocator.name + "-" + gimp_test.name + "-brk-parsed.csv")

        mmap_reader = csv.reader(mmap_file)
        munmap_reader = csv.reader(munmap_file)
        brk_reader = csv.reader(brk_file)
        next(mmap_reader)
        next(munmap_reader)
        next(brk_reader)

        mmap_sizes = [math.log(int(i[5])) for i in mmap_reader]
        plt.hist(mmap_sizes, bins=100, log=True)

        plt.ylabel('Count')
        plt.xlabel('Log(Memory)')
        plt.savefig(
            "output/" + self.allocator.name + "-" + gimp_test.name + "-" + GraphName.STRACE_MEMORY_COUNT_HIST.name)

    def plot_proc_page_faults(self, gimp_test: GimpTestName):
        fault_file = open(
            "input/" + self.allocator.name + "-" + gimp_test.name + "-" + GraphName.PROC_PAGE_FAULTS.name + ".csv")
        fault_csv = csv.reader(fault_file)
        next(fault_csv)

        minflt, cminflt, timestamps, min_time = [], [], [], None
        for row in fault_csv:
            if min_time is None: min_time = row[1]
            timestamps.append(int(row[1]) - int(min_time))
            minflt.append(int(row[2]))
            cminflt.append(int(row[3]))

        plt.plot(timestamps, minflt, label="minflt")
        plt.plot(timestamps, cminflt, label="cminflt")
        plt.legend()
        plt.savefig("output/" + self.allocator.name + "-" + gimp_test.name + "-" + GraphName.PROC_PAGE_FAULTS.name)

    def plot_memory_consumed(self, gimp_test: GimpTestName):
        fault_file = open(
            "input/" + self.allocator.name + "-" + gimp_test.name + "-" + GraphName.PROC_MEMORY_CONSUMPTION.name + ".csv")
        memuse_csv = csv.reader(fault_file)
        next(memuse_csv)

        memuse, timestamps, min_time = [], [], None
        for row in memuse_csv:
            if min_time is None: min_time = row[1]
            timestamps.append(int(row[1]) - int(min_time))
            memuse.append(int(row[2]))

        plt.plot(timestamps, memuse)
        plt.savefig(
            "output/" + self.allocator.name + "-" + gimp_test.name + "-" + GraphName.PROC_MEMORY_CONSUMPTION.name)


def save_file(file):
    file.flush()
    os.fsync(file.fileno())


def exec_shell_cmd(cmd):
    stream = os.popen(cmd)
    return stream.read()


def count_page_faults(pid):
    pid = pid.replace('\n', '')
    return exec_shell_cmd('cat /proc/' + pid + '/stat').strip().split(" ")[9:13]


def count_memory_consumed(pid):
    pid = pid.replace('\n', '')
    return os.popen(
        "sudo cat /proc/" + pid + "/smaps | grep -i pss |  awk '{Total+=$2} END {print Total}'").read().strip()


class Collector:

    def __init__(self, allocator: AllocatorName):
        self.allocator = allocator
        self.poll_interval = 0.3

    def collect_logs(self):
        for gimp_test in GimpTestName:
            if gimp_test != GimpTestName.UNSHARP: continue

            print("# COLLECTING FAULTS FOR", gimp_test.name)
            # self.collect_faults(gimp_test)

            print("# COLLECTING MEMUSE FOR", gimp_test.name)
            # self.collect_memory_consumption(gimp_test)

            self.collect_strace(gimp_test)
            print("# COLLECTED STRACE")

    def collect_strace(self, gimp_test: GimpTestName):
        strace_path = "input/" + self.allocator.name + "-" + gimp_test.name + "-strace.txt"
        exec_shell_cmd(
            ALLOCATOR_CMD_PREFIX_MAP[allocator] + " sudo strace -T -tt -o " + strace_path + " -q -e trace=memory -f " +
            TEST_CMD_MAP[gimp_test])

        strace_file = open(strace_path, "r")
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
            parsed_file_name = "input/" + self.allocator.name + "-" + gimp_test.name + "-" + call_name + "parsed.csv"
            call_results_file = open(parsed_file_name, "w")
            mmap_csv = csv.writer(call_results_file)
            mmap_csv.writerows(syscall_results_map[call_name])
            call_results_file.close()

    def collect_memory_consumption(self, gimp_test: GimpTestName):
        memory_csv_path = "input/" + self.allocator.name + "-" + gimp_test.name + "-" + GraphName.PROC_MEMORY_CONSUMPTION.name + ".csv"
        memory_csv_file = open(memory_csv_path, "w")
        memory_csv_writer = csv.writer(memory_csv_file)
        memory_csv_writer.writerow(['pid', 'time', 'mem'])

        subprocess.Popen(ALLOCATOR_CMD_PREFIX_MAP[allocator] + " " + TEST_CMD_MAP[gimp_test], shell=True)

        while True:
            print(".", end="", flush=True)
            gimp_pid = exec_shell_cmd('pidof gimp').replace("\n", "")
            if not gimp_pid: break
            try:
                row = count_memory_consumed(gimp_pid)
                if row: memory_csv_writer.writerow([gimp_pid, time.time_ns(), row])
            except:
                pass

            save_file(memory_csv_file)
            time.sleep(self.poll_interval)

        memory_csv_file.close()

    def collect_faults(self, gimp_test: GimpTestName):
        fault_csv_path = "input/" + self.allocator.name + "-" + gimp_test.name + "-" + GraphName.PROC_PAGE_FAULTS.name + ".csv"
        faults_csv_file = open(fault_csv_path, "w")
        faults_csv_writer = csv.writer(faults_csv_file)
        faults_csv_writer.writerow(['gimp-pid', 'time', 'minflt', 'cminflt', 'majflt', 'cmajflt'])

        subprocess.Popen(ALLOCATOR_CMD_PREFIX_MAP[allocator] + " " + TEST_CMD_MAP[gimp_test], shell=True)

        while True:
            print(".", end="", flush=True)
            gimp_pid = exec_shell_cmd('pidof gimp').replace("\n", "")
            if not gimp_pid: break
            try:
                row = count_page_faults(gimp_pid)
                if len(row) != 4: continue
                faults_csv_writer.writerow([gimp_pid, time.time_ns()] + row)
            except:
                pass

            save_file(faults_csv_file)
            time.sleep(self.poll_interval)

        faults_csv_file.close()


def parse_call(syscall, fn_name):
    pid, timestamp, ret_val, duration = get_fields(syscall)
    fn_args_list = get_fn_arguments(syscall, fn_name)
    return [pid, timestamp, ret_val, duration] + fn_args_list


def get_fields(syscall):
    syscall = syscall.replace("\n", "")
    res = syscall.split(" ")
    return res[0], res[1], res[-2], res[-1]


def get_fn_arguments(syscall, fn_name):
    pattern = re.compile("(?<=" + fn_name + "\().*(?=\))")
    fn_args_str = pattern.findall(syscall)[0]
    fn_args_list = [i.strip() for i in fn_args_str.split(",")]
    return fn_args_list


def parse_call_for_unfinished(syscall, fn_name):
    pid, timestamp = get_fields_for_unfinished(syscall)
    fn_args_list = get_fn_arguments_for_unfinished(syscall, fn_name)
    return [pid, timestamp] + fn_args_list


def get_fields_for_unfinished(syscall):
    syscall = syscall.replace("\n", "")
    res = syscall.split(" ")
    return res[0], res[1]


def get_fn_arguments_for_unfinished(syscall, fn_name):
    pattern = re.compile("(?<=" + fn_name + "\().*(?=\<)")
    fn_args_str = pattern.findall(syscall)[0]
    fn_args_list = [i.strip() for i in fn_args_str.split(",")]
    return fn_args_list


def get_fields_for_resumed(syscall):
    syscall = syscall.replace("\n", "")
    res = syscall.split(" ")
    return res[0], res[-2], res[-1]


if __name__ == "__main__":
    for allocator in AllocatorName:
        print("# RUNNING WITH ALLOCATOR: ", allocator.name)
        if allocator != AllocatorName.LIB_C: continue

        collector = Collector(allocator)
        collector.collect_logs()

        grapher = Graph(allocator)
        grapher.plot()
