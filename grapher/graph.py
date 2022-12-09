from enum import Enum
import subprocess
import csv
import os
import time


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


class Graph:

    def __init__(self, allocator: AllocatorName, gimp_test: str, graph_name: GraphName):
        self.allocator = allocator
        self.gimp_test = gimp_test
        self.graph_name = graph_name

    def plot(self):
        if self.graph_name == GraphName.PROC_PAGE_FAULTS:
            pass
        elif self.graph_name == GraphName.PROC_MEMORY_CONSUMPTION:
            pass
        elif self.graph_name == GraphName.STRACE_MEMORY_COUNT_HIST:
            pass
        elif self.graph_name == GraphName.STRACE_MEMORY_MEMORY_HIST:
            pass


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

    def __init__(self, gimp_test: GimpTestName):
        self.gimp_test = gimp_test
        self.poll_interval = 0.3

        # Initialize CSV for page fault data
        self.fault_csv_path = "input/" + self.gimp_test.name + "-faults.csv"
        self.faults_csv_file = open(self.fault_csv_path, "w")
        self.faults_csv_writer = csv.writer(self.faults_csv_file)
        self.faults_csv_writer.writerow(['gimp-pid', 'time', 'minflt', 'cminflt', 'majflt', 'cmajflt'])

    def collect_faults(self):
        subprocess.Popen([TEST_CMD_MAP[self.gimp_test]])

        start_time = None
        while True:
            gimp_pid = exec_shell_cmd('pidof gimp').replace("\n", "")
            print("Found gimp:", gimp_pid)
            if not gimp_pid: break
            try:
                row = count_page_faults(gimp_pid)
                if len(row) != 4: continue
                if start_time is None: start_time = time.time_ns()
                self.faults_csv_writer.writerow([gimp_pid, start_time - time.time_ns()] + row)
            except: pass

            save_file(self.faults_csv_file)
            time.sleep(self.poll_interval)

        self.faults_csv_file.close()


if __name__ == "__main__":
    collector = Collector(GimpTestName.UNSHARP)
    collector.collect_faults()
