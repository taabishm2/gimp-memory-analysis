import matplotlib.pyplot as plt
from enum import Enum
import subprocess
import time
import csv
import os
import re
import math
from collections import Counter

DPI = 500


class GraphName(Enum):
    PROC_PSS_MEMORY_CONSUMPTION = 1
    PROC_RSS_MEMORY_CONSUMPTION = 2
    PROC_PAGE_FAULTS = 3
    PROC_PAGE_FAULTS_GRID = 4
    STRACE_MEMORY_COUNT_HIST = 5
    STRACE_MEMORY_MEMORY_HIST = 6
    PROC_FRAGMENTS = 7
    RUN_TIME = 8


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
    GimpTestName.UNSHARP: """ gimp -i -b '(batch-unsharp-mask "*JPG" 15.0 0.6 0)' -b '(gimp-quit 0)' """,
    GimpTestName.RESIZE: """ gimp -i -b '(batch-resize-image "*JPG" 600 400)' -b '(gimp-quit 0)' """,
    GimpTestName.ROTATE: """ gimp -i -b '(batch-rotate "*JPG")' -b '(gimp-quit 0)' """,
    GimpTestName.AUTO_LEVEL: """ gimp -i -b '(batch-auto-levels "*JPG")' -b '(gimp-quit 0)' """
}

ALLOCATOR_CMD_PREFIX_MAP = {
    AllocatorName.LIB_C: "",
    AllocatorName.TC_MALLOC: "LD_PRELOAD=/store/gperftools-2.10/out/libtcmalloc.so",
    AllocatorName.MI_MALLOC: "LD_PRELOAD=/usr/local/lib/libmimalloc.so",
    AllocatorName.TBB_MALLOC: "LD_PRELOAD=/tmp/my_installed_onetbb/lib/libtbbmalloc.so",
    AllocatorName.JE_MALLOC: "LD_PRELOAD=/usr/local/lib/libjemalloc.so"
}


class Graph:

    def plot(self):
        for gimp_test in [GimpTestName.UNSHARP]:
            plt.clf()

            for allocator in ALLOCATOR_CMD_PREFIX_MAP:
                print(" *****   PLOTTING FAULTS FOR", gimp_test.name, allocator.name)
                self.plot_proc_page_faults(gimp_test, allocator)
            plt.clf()

            for allocator in ALLOCATOR_CMD_PREFIX_MAP:
                print(" *****   PLOTTING FAULTS-GRID FOR", gimp_test.name, allocator.name)
                self.plot_proc_page_faults_grid(gimp_test, allocator)
            plt.clf()

            for allocator in ALLOCATOR_CMD_PREFIX_MAP:
                print(" *****   PLOTTING PSS-MEMUSE FOR", gimp_test.name, allocator.name)
                self.plot_pss_memory_consumed(gimp_test, allocator)
            plt.clf()

            for allocator in ALLOCATOR_CMD_PREFIX_MAP:
                print(" *****   PLOTTING RSS-MEMUSE FOR", gimp_test.name, allocator.name)
                self.plot_rss_memory_consumed(gimp_test, allocator)
            plt.clf()

            for allocator in ALLOCATOR_CMD_PREFIX_MAP:
                print(" *****   PLOTTING MEM-CNT FOR", gimp_test.name, allocator.name)
                self.plot_memory_memory_count(gimp_test, allocator)
            plt.clf()

            for allocator in ALLOCATOR_CMD_PREFIX_MAP:
                print(" *****   PLOTTING MEM-MEM FOR", gimp_test.name, allocator.name)
                self.plot_memory_memory_size(gimp_test, allocator)
            plt.clf()

            for allocator in ALLOCATOR_CMD_PREFIX_MAP:
                print(" *****   PLOTTING TIME CONSUMED", gimp_test.name, allocator.name)
                self.plot_time_consumed(gimp_test, allocator)
            plt.clf()

            for allocator in ALLOCATOR_CMD_PREFIX_MAP:
                print(" *****   PLOTTING FRAGMENTS", gimp_test.name, allocator.name)
                self.plot_fragments(gimp_test, allocator)
            plt.clf()

            for allocator in ALLOCATOR_CMD_PREFIX_MAP:
                print(" *****   PLOTTING KERNEL CROSSING FOR", gimp_test.name, allocator.name)
                self.plot_mem_kernel_cross(gimp_test, allocator)
            plt.clf()

    def plot_mem_kernel_cross(self, gimp_test: GimpTestName, allocator: AllocatorName):
        mmap_file = open("input/" + allocator.name + "-" + gimp_test.name + "-mmap-parsed.csv")
        munmap_file = open("input/" + allocator.name + "-" + gimp_test.name + "-munmap-parsed.csv")
        brk_file = open("input/" + allocator.name + "-" + gimp_test.name + "-brk-parsed.csv")

        mmap_reader = csv.reader(mmap_file)
        munmap_reader = csv.reader(munmap_file)
        brk_reader = csv.reader(brk_file)
        next(mmap_reader)
        next(munmap_reader)
        next(brk_reader)

        mmap_count = len([row for row in mmap_reader])
        munmap_count = len([row for row in munmap_reader])
        brk_count = len([row for row in brk_reader])

        print("MMAP", allocator.name, mmap_count)
        print("MUNMAP", allocator.name, munmap_count)
        print("BRK", allocator.name, brk_count)

    def plot_fragments(self, gimp_test: GimpTestName, allocator: AllocatorName):
        fragments_file = open(
            "input/" + allocator.name + "-" + gimp_test.name + "-" + GraphName.PROC_FRAGMENTS.name + ".csv")
        fragments_csv = csv.reader(fragments_file)
        next(fragments_csv)

        faults, timestamps, min_time = [], [], None
        for row in fragments_csv:
            if min_time is None: min_time = row[1]
            timestamps.append((int(row[1]) - int(min_time)) / pow(10, 9))
            faults.append((int(row[2])))

        plt.plot(timestamps, faults, label=allocator.name)
        plt.ylim(500, 1750)
        plt.title("Count of virtual memory fragments vs time elapsed")
        #plt.grid(True, linestyle="--", alpha=0.5)
        plt.legend()
        plt.xlabel("Time elapsed (sec)")
        plt.ylabel("Count of fragments")
        plt.savefig(
            "output/" + allocator.name + "-" + gimp_test.name + "-" + GraphName.PROC_FRAGMENTS.name, dpi=DPI)

    def plot_time_consumed(self, gimp_test: GimpTestName, allocator: AllocatorName):
        time_file = open(
            "input/" + allocator.name + "-" + gimp_test.name + "-" + GraphName.RUN_TIME.name + ".csv")
        time_csv = csv.reader(time_file)
        rows = [r for r in time_csv]

        plt.bar([allocator.name], -int(rows[1][0]) / pow(10, 9), width=0.5)

        plt.title("Total execution time")
        #plt.grid(True, linestyle="--", alpha=0.5)
        plt.xlabel("Allocator")
        plt.ylabel("Run time (sec)")
        plt.savefig(
            "output/" + allocator.name + "-" + gimp_test.name + "-" + GraphName.RUN_TIME.name, dpi=DPI)

    def plot_memory_memory_size(self, gimp_test: GimpTestName, allocator: AllocatorName):
        mmap_file = open("input/" + allocator.name + "-" + gimp_test.name + "-mmap-parsed.csv")
        munmap_file = open("input/" + allocator.name + "-" + gimp_test.name + "-munmap-parsed.csv")
        brk_file = open("input/" + allocator.name + "-" + gimp_test.name + "-brk-parsed.csv")

        mmap_reader = csv.reader(mmap_file)
        munmap_reader = csv.reader(munmap_file)
        brk_reader = csv.reader(brk_file)
        next(mmap_reader)
        next(munmap_reader)
        next(brk_reader)

        bin_size = 6000000
        mmap_sizes = [int(i[5]) for i in mmap_reader]
        bins = max(mmap_sizes) // bin_size + 1
        x_vals, y_vals = [], [0] * bins

        for val in mmap_sizes:
            y_vals[int(val) % bins] += val
        y_vals = [y for y in y_vals]

        plt.bar([i for i in range(bins)], y_vals, alpha=0.5, label=allocator.name)
        # print(interval_size,[(interval_size * i) + (interval_size // 2) for i in range(bins)])
        # plt.bar([(interval_size * i) + (interval_size // 2) for i in range(bins)], hist, alpha=0.5, label=allocator.name, width=0.5)

        plt.title("Total allocated memory by mmap request sizes")
        #plt.grid(True, linestyle="--", alpha=0.5)
        plt.ylabel('Total allocated memory')
        plt.xlabel('Size of memory request (bytes)')
        plt.legend()
        plt.savefig(
            "output/" + allocator.name + "-" + gimp_test.name + "-" + GraphName.STRACE_MEMORY_MEMORY_HIST.name, dpi=DPI)

    def plot_memory_memory_count(self, gimp_test: GimpTestName, allocator: AllocatorName):
        mmap_file = open("input/" + allocator.name + "-" + gimp_test.name + "-mmap-parsed.csv")
        munmap_file = open("input/" + allocator.name + "-" + gimp_test.name + "-munmap-parsed.csv")
        brk_file = open("input/" + allocator.name + "-" + gimp_test.name + "-brk-parsed.csv")

        mmap_reader = csv.reader(mmap_file)
        munmap_reader = csv.reader(munmap_file)
        brk_reader = csv.reader(brk_file)
        next(mmap_reader)
        next(munmap_reader)
        next(brk_reader)

        merged_values, top_addr_map = [], dict()
        for row in mmap_reader:
            merged_values.append(int(row[5]))
        # for row in munmap_reader:
        #     merged_values.append(-int(row[5]))
        for row in brk_reader:
            if row[0] not in top_addr_map: top_addr_map[row[0]] = row[2]
            if row[4] == "NULL": continue
            top_addr, new_top = top_addr_map[row[0]], row[4]
            memory_diff = int(new_top, 16) - int(top_addr, 16)
            if memory_diff < 0: continue
            merged_values.append(memory_diff)
            top_addr_map[row[0]] = row[2]

        # bin_size = 6000000
        # mmap_sizes = [int(i[5]) for i in mmap_reader]
        # for i in munmap_reader
        # bins = max(mmap_sizes) // bin_size + 1
        # x_vals, y_vals = [], [0] * bins
        #
        # for val in mmap_sizes:
        #     y_vals[int(val) % bins] += 1
        # y_vals = [y for y in y_vals]

        #plt.bar([i for i in range(bins)], y_vals, alpha=0.5, label=allocator.name)
        print(sorted(merged_values[:100]))
        plt.hist(merged_values, label=allocator.name, alpha=0.5, bins=50)

        plt.title("Count of mmap requests vs memory requested")
        #plt.grid(True, linestyle="--", alpha=0.5)
        plt.xlim(0.5)
        plt.ylabel('Count of calls')
        plt.xlabel('Size of memory request (bytes)')
        plt.legend()
        plt.savefig(
            "output/" + allocator.name + "-" + gimp_test.name + "-" + GraphName.STRACE_MEMORY_COUNT_HIST.name, dpi=DPI)
    def plot_proc_page_faults(self, gimp_test: GimpTestName, allocator: AllocatorName):
        fault_file = open(
            "input/" + allocator.name + "-" + gimp_test.name + "-" + GraphName.PROC_PAGE_FAULTS.name + ".csv")
        fault_csv = csv.reader(fault_file)
        next(fault_csv)

        # Sums up minflts and cminflts (minor faults of proces and waited-on children)
        faults, timestamps, min_time = [], [], None
        for row in fault_csv:
            if min_time is None: min_time = row[1]
            timestamps.append((int(row[1]) - int(min_time)) / pow(10, 9))
            faults.append((int(row[2]) + int(row[3])) / pow(10, 6))

        plt.plot(timestamps, faults, label=allocator.name)
        plt.legend()
        plt.title("Page faults vs time elapsed")
        #plt.grid(True, linestyle="--", alpha=0.5)
        plt.xlabel("Time elapsed (sec)")
        plt.ylabel("Count of page faults (millions)")
        plt.savefig(
            "output/" + allocator.name + "-" + gimp_test.name + "-" + GraphName.PROC_PAGE_FAULTS.name, dpi=DPI)

    def plot_proc_page_faults_grid(self, gimp_test: GimpTestName, allocator: AllocatorName):
        fault_file = open(
            "input/" + allocator.name + "-" + gimp_test.name + "-" + GraphName.PROC_PAGE_FAULTS.name + ".csv")
        fault_csv = csv.reader(fault_file)
        rows = [r for r in fault_csv]
        first, last = rows[1], rows[-1]

        x, y = (int(last[1]) - int(first[1])) / pow(10, 9), ((int(last[2]) + int(last[3])) / pow(10, 6))
        plt.plot(x, y, marker="o", label=allocator.name)
        plt.legend()
        plt.title("Completion time vs page faults")
        #plt.grid(True, linestyle="--", alpha=0.5)
        plt.xlabel("completion time (sec)")
        plt.ylabel("Count of page faults (millions)")
        plt.savefig(
            "output/" + allocator.name + "-" + gimp_test.name + "-" + GraphName.PROC_PAGE_FAULTS_GRID.name, dpi=DPI)

    def plot_pss_memory_consumed(self, gimp_test: GimpTestName, allocator: AllocatorName):
        fault_file = open(
            "input/" + allocator.name + "-" + gimp_test.name + "-" + GraphName.PROC_PSS_MEMORY_CONSUMPTION.name + ".csv")
        memuse_csv = csv.reader(fault_file)
        next(memuse_csv)

        memuse, timestamps, min_time = [], [], None
        for row in memuse_csv:
            if min_time is None: min_time = row[1]
            timestamps.append((int(row[1]) - int(min_time)) / pow(10, 9))
            memuse.append(int(row[2]) / (1024 * 1024))

        plt.plot(timestamps, memuse, label=allocator.name)
        plt.legend()
        plt.title("Memory consumed with time (PSS)")
        #plt.grid(True, linestyle="--", alpha=0.5)
        plt.xlabel("Time elapsed (sec)")
        plt.ylabel("Memory consumed - PSS (MB)")
        plt.savefig(
            "output/" + allocator.name + "-" + gimp_test.name + "-" + GraphName.PROC_PSS_MEMORY_CONSUMPTION.name,
            dpi=DPI)

    def plot_rss_memory_consumed(self, gimp_test: GimpTestName, allocator: AllocatorName):
        fault_file = open(
            "input/" + allocator.name + "-" + gimp_test.name + "-" + GraphName.PROC_RSS_MEMORY_CONSUMPTION.name + ".csv")
        memuse_csv = csv.reader(fault_file)
        next(memuse_csv)

        memuse, timestamps, min_time = [], [], None
        for row in memuse_csv:
            if min_time is None: min_time = row[1]
            timestamps.append((int(row[1]) - int(min_time)) / pow(10, 9))
            memuse.append(int(row[2]) / (1024 * 1024))

        plt.plot(timestamps, memuse, label=allocator.name)
        plt.legend()
        plt.title("Memory consumed with time (RSS)")
        plt.xlabel("Time elapsed (sec)")
        plt.ylabel("Memory consumed - RSS (MB)")
        plt.savefig(
            "output/" + allocator.name + "-" + gimp_test.name + "-" + GraphName.PROC_RSS_MEMORY_CONSUMPTION.name,
            dpi=DPI)


def save_file(file):
    file.flush()
    os.fsync(file.fileno())


def exec_shell_cmd(cmd):
    stream = os.popen(cmd)
    return stream.read()


def count_page_faults(pid):
    pid = pid.replace('\n', '')
    pid = pid.strip()
    return exec_shell_cmd('cat /proc/' + pid + '/stat').strip().split(" ")[9:13]


def count_fragments(pid):
    pid = pid.replace('\n', '')
    pid = pid.strip()
    return exec_shell_cmd('cat /proc/' + pid + '/maps | wc -l').strip()


def count_memory_consumed(pid, type):
    pid = pid.replace('\n', '')
    pid = pid.strip()
    return os.popen(
        "sudo cat /proc/" + pid + "/smaps | grep -i " + type + " |  awk '{Total+=$2} END {print Total*1024}'").read().strip()


class Collector:

    def __init__(self, allocator: AllocatorName):
        self.allocator = allocator
        self.poll_interval = 0.1

    def collect_logs(self):
        for gimp_test in GimpTestName:
            print(" *****   COLLECTING MEMUSE, FAULTS, FRAGMENTS FOR", gimp_test.name, "with", self.allocator.name)
            self.collect_proc_data(gimp_test)

            print(" *****   COLLECTING STRACE FOR", gimp_test.name, "with", self.allocator.name)
            self.collect_strace(gimp_test)

    def collect_strace(self, gimp_test: GimpTestName):
        strace_path = "input/" + self.allocator.name + "-" + gimp_test.name + "-strace.txt"
        exec_shell_cmd(
            "sudo " + ALLOCATOR_CMD_PREFIX_MAP[self.allocator] +
            " strace -T -tt -o " + strace_path + " -q -e trace=memory -f " +
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
            parsed_file_name = "input/" + self.allocator.name + "-" + gimp_test.name + "-" + call_name + "-parsed.csv"
            call_results_file = open(parsed_file_name, "w")
            mmap_csv = csv.writer(call_results_file)
            mmap_csv.writerows(syscall_results_map[call_name])
            call_results_file.close()

    def get_csv_with_writer(self, gimp_test: GimpTestName, graphName: GraphName, headers: list):
        csv_path = "input/" + self.allocator.name + "-" + gimp_test.name + "-" + graphName.name + ".csv"
        csv_file = open(csv_path, "w")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(headers)
        return csv_file, csv_writer

    def collect_proc_data(self, gimp_test: GimpTestName):
        time_consumed = time.time_ns()
        pss_memory_csv_file, pss_memory_csv_writer = self.get_csv_with_writer(gimp_test,
                                                                              GraphName.PROC_PSS_MEMORY_CONSUMPTION,
                                                                              ['pid', 'time', 'mem'])
        rss_memory_csv_file, rss_memory_csv_writer = self.get_csv_with_writer(gimp_test,
                                                                              GraphName.PROC_RSS_MEMORY_CONSUMPTION,
                                                                              ['pid', 'time', 'mem'])
        faults_csv_file, faults_csv_writer = self.get_csv_with_writer(gimp_test, GraphName.PROC_PAGE_FAULTS,
                                                                      ['gimp-pid', 'time', 'minflt', 'cminflt',
                                                                       'majflt', 'cmajflt'])
        fragments_csv_file, fragments_csv_writer = self.get_csv_with_writer(gimp_test, GraphName.PROC_FRAGMENTS,
                                                                            ['gimp-pid', 'time', 'fragments'])
        timing_csv_file, timing_csv_writer = self.get_csv_with_writer(gimp_test, GraphName.RUN_TIME, ['time'])

        subprocess.Popen(ALLOCATOR_CMD_PREFIX_MAP[self.allocator] + " " + TEST_CMD_MAP[gimp_test], shell=True)

        while True:
            print(".", end="", flush=True)
            gimp_pid = exec_shell_cmd('pidof gimp').replace("\n", "")
            if not gimp_pid:
                time_consumed -= time.time_ns()
                timing_csv_writer.writerow([time_consumed])
                break
            try:
                pss_row = count_memory_consumed(gimp_pid, "pss")
                rss_row = count_memory_consumed(gimp_pid, "rss")
                faults_row = count_page_faults(gimp_pid)
                fragments_row = count_fragments(gimp_pid)
                if pss_row: pss_memory_csv_writer.writerow([gimp_pid, time.time_ns(), pss_row])
                if rss_row: rss_memory_csv_writer.writerow([gimp_pid, time.time_ns(), rss_row])
                if fragments_row: fragments_csv_writer.writerow([gimp_pid, time.time_ns(), fragments_row])
                if len(faults_row) == 4: faults_csv_writer.writerow([gimp_pid, time.time_ns()] + faults_row)
            except:
                pass

            time.sleep(self.poll_interval)

        pss_memory_csv_file.close()
        rss_memory_csv_file.close()
        faults_csv_file.close()
        fragments_csv_file.close()
        timing_csv_file.close()


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
    for allocator in ALLOCATOR_CMD_PREFIX_MAP:
        print(" *****   COLLECTING WITH ALLOCATOR: ", allocator.name)

        collector = Collector(allocator)
        collector.collect_logs()

    # print(" *****   STARTING PLOT")
    # grapher = Graph()
    # grapher.plot()

    print(" *****   DONE")
