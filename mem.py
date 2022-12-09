import os
import csv
import time
from collections import defaultdict
import matplotlib.pyplot as plt

def get_memory(pid):
    pid = pid.replace('\n','')
    stream = os.popen("sudo cat /proc/" + pid + "/smaps | grep -i pss |  awk '{Total+=$2} END {print Total}'")
    output = stream.read()
    if output.strip() == "":
        raise Exception
    return output

def plot_memory():
    o = open("./strace_logs/memory.csv")
    o_reader = csv.reader(o)

    mem_use = defaultdict(list)
    maj_times = defaultdict(list)

    timestamps = []
    o_reader = [r for r in o_reader]
    start_time = None
    prev_test = None
    for row in o_reader[1:]:
        if int(row[0]) != prev_test:
            start_time = int(row[1])
            if prev_test is not None:
                maj_times[prev_test] = timestamps.copy()
                timestamps.clear()
        prev_test = int(row[0])

        mem_use[int(row[0])].append(int(row[2].replace("\n","")))
        if start_time is None: start_time = int(row[3])
        timestamps.append(int(row[1]) - int(start_time))
    maj_times[prev_test] = timestamps.copy()
    for i in mem_use:print(i, len(mem_use[i]), mem_use[i])
    for i in maj_times:print(i, len(maj_times[i]), maj_times[i])

    for test in mem_use:
        plt.plot(maj_times[test], mem_use[test])
        plt.savefig('graphs/resize-memory-consumption')

plot_memory()
if __name__ == "__dmain__":
    #plot_faults()

    memory = open("memory.csv", "w")
    f_writer = csv.writer(memory)
    f_writer.writerow(['pid', 'time', 'mem'])
    memory.close()

    gimp_pid = None
    pids_to_track = set()
    stopped_pids = set()
    search_count = 0

    while True:
        #print("#", search_count, "searching...")
        search_count += 1
        time.sleep(0.1)

        memory = open("memory.csv", "a")
        f_writer = csv.writer(memory)

        stream = os.popen('pidof gimp')
        gimp_pid = stream.read()
        gimp_pid = gimp_pid.replace("\n", "")
        if not gimp_pid: continue
        #print("Found GIMP", gimp_pid)

        pids_to_track.add((gimp_pid, gimp_pid))

        for p in pids_to_track:
            if p[0] in stopped_pids: continue
            #print("Counting for PID:", p[0])
            try:
                row = get_memory(p[0])
                #print("Found:", [gimp_pid, p[0], p[1]] + row)
                f_writer.writerow([gimp_pid, time.time_ns(), row])
            except:
                #print("FAILED")
                # PID isn't active anymore
                stopped_pids.add(p[0])
                memory.close()
                memory = open("faults.csv", "a")
                f_writer = csv.writer(memory)

    memory.close()
