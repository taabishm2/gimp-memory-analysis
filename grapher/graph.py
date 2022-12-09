from collections import defaultdict
import matplotlib.pyplot as plt
from enum import Enum
import subprocess
import time
import csv
import os


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
            print("# PLOTTING FAULTS FOR", gimp_test.name)
            if gimp_test != GimpTestName.UNSHARP: continue
            self.plot_proc_page_faults(gimp_test)

    def plot_proc_page_faults(self, gimp_test: GimpTestName):
        fault_file = open("input/" + self.allocator.name + "-" + gimp_test.name + "-" + GraphName.PROC_PAGE_FAULTS.name + ".csv")
        fault_csv = csv.reader(fault_file)
        next(fault_csv)

        minflt, cminflt, timestamps, min_time = [], [], [], None
        for row in fault_csv:
            if min_time is None: min_time = row[1]
            timestamps.append(row[1] - min_time)
            minflt.append(row[2])
            cminflt.append(row[3])

        plt.plot(timestamps, minflt)
        plt.plot(timestamps, cminflt)
        plt.savefig("output/" + self.allocator.name + "-" + gimp_test.name + "-" + GraphName.PROC_PAGE_FAULTS.name)


def save_file(file):
    file.flush()
    os.fsync(file.fileno())


def exec_shell_cmd(cmd):
    stream = os.popen(cmd)
    return stream.read()


def count_page_faults(pid):
    pid = pid.replace('\n', '')
    return exec_shell_cmd('cat /proc/' + pid + '/stat').strip().split(" ")[9:13]


class Collector:

    def __init__(self, allocator: AllocatorName):
        self.allocator = allocator
        self.poll_interval = 0.3

    def collect_all_faults(self):
        for gimp_test in GimpTestName:
            print("# COLLECTING FAULTS FOR", gimp_test.name)
            if gimp_test != GimpTestName.UNSHARP: continue
            self.collect_faults(gimp_test)

    def collect_faults(self, gimp_test: GimpTestName):
        fault_csv_path = "input/" + self.allocator.name + "-" + gimp_test.name + "-" + GraphName.PROC_PAGE_FAULTS.name + ".csv"
        faults_csv_file = open(fault_csv_path, "w")
        faults_csv_writer = csv.writer(faults_csv_file)
        faults_csv_writer.writerow(['gimp-pid', 'time', 'minflt', 'cminflt', 'majflt', 'cmajflt'])
        
        subprocess.Popen(TEST_CMD_MAP[gimp_test], shell=True)

        while True:
            print(".", end="", flush=True)
            gimp_pid = exec_shell_cmd('pidof gimp').replace("\n", "")
            if not gimp_pid: break
            try:
                row = count_page_faults(gimp_pid)
                if len(row) != 4: continue
                faults_csv_writer.writerow([gimp_pid, time.time_ns()] + row)
            except: pass

            save_file(faults_csv_file)
            time.sleep(self.poll_interval)

        faults_csv_file.close()


if __name__ == "__main__":
    for allocator in AllocatorName:
        print("# RUNNING WITH ALLOCATOR: ", allocator.name)
        if allocator != AllocatorName.LIB_C: continue

        collector = Collector(allocator)
        collector.collect_all_faults()

        grapher = Graph(allocator)
        grapher.plot()
