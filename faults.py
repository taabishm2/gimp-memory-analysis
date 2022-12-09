import os
import csv
import time
from collections import defaultdict
import matplotlib.pyplot as plt

def count_page_faults(pid):
    pid = pid.replace('\n','')
    stream = os.popen('cat /proc/' + pid + '/stat')
    output = stream.read()
    if output.strip() == "":
        raise Exception
    return output.split(" ")[9:13]

def plot_faults():
    o = open("./strace_logs/faults.csv")
    o_reader = csv.reader(o)

    maj_counts = defaultdict(list)
    maj_times = defaultdict(list)

    timestamps = []
    o_reader = [r for r in o_reader]
    start_time = None
    prev_test = None
    for row in o_reader:
        if row[0] == row[1]:
            if int(row[0]) != prev_test:
                start_time = int(row[3])
                if prev_test is not None:
                    maj_times[prev_test] = timestamps.copy()
                    timestamps.clear()
            prev_test = int(row[0])

            maj_counts[int(row[0])].append(int(row[4]))
            if start_time is None: start_time = int(row[3])
            timestamps.append(int(row[3]) - int(start_time))
    maj_times[prev_test] = timestamps.copy()
    for i in maj_counts:print(i, len(maj_counts[i]), maj_counts[i])
    for i in maj_times:print(i, len(maj_times[i]), maj_times[i])

    for test in maj_counts:
        plt.plot(maj_times[test], maj_counts[test])
    plt.savefig('graphs/unsharp-pagefaults')

plot_faults()
if __name__ == "__masin__":
    #plot_faults()

    faults = open("faults.csv", "w")
    f_writer = csv.writer(faults)
    f_writer.writerow(['gimp-pid', 'pid', 'ppid', 'time', 'minflt', 'cminflt', 'majflt', 'cmajflt'])
    faults.close()

    gimp_pid = None
    pids_to_track = set()
    stopped_pids = set()
    search_count = 0

    while True:
        print("#", search_count, "searching...")
        search_count += 1
        time.sleep(0.3)

        faults = open("faults.csv", "a")
        f_writer = csv.writer(faults)

        stream = os.popen('pidof gimp')
        gimp_pid = stream.read()
        gimp_pid = gimp_pid.replace("\n", "")
        if not gimp_pid: continue

        pids_to_track.add((gimp_pid, gimp_pid))

        child_pids = set()
        for pid_entry in pids_to_track:
            continue
            # Get child process from parent process ID: ps --ppid <PPID> -o pid,ppid
            #print("Checking", pid_entry, "from", pids_to_track)
            #print('ps --ppid ' + str(pid_entry[0]) + ' -o pid,ppid')
            stream = os.popen('ps --ppid ' + str(pid_entry[0]) + ' -o pid,ppid --no-header')
            stream_res = stream.read()
            #print(stream_res)

            child_pid_list = stream_res.split("\n")
            for child in child_pid_list:
                stripped_child = [i for i in child.strip().split(" ") if i.strip()]
                if not child or not stripped_child[0]: continue

                child_pids.add(tuple(stripped_child))

        pids_to_track = pids_to_track.union(child_pids)

        for p in pids_to_track:
            if p[0] in stopped_pids: continue
            #print("Counting for PID:", p[0])
            try:
                row = count_page_faults(p[0])
                if len(row) != 4: break
                #print("Found:", [gimp_pid, p[0], p[1]] + row)
                f_writer.writerow([gimp_pid, p[0], p[1], time.time_ns()] + row)
            except:
                #print("FAILED")
                # PID isn't active anymore
                stopped_pids.add(p[0])
                faults.close()
                faults = open("faults.csv", "a")
                f_writer = csv.writer(faults)

    faults.close()
