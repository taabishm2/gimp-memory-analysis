import os
import csv
import time

def count_page_faults(pid):
    pid = pid.replace('\n','')
    stream = os.popen('cat /proc/' + pid + '/stat')
    output = stream.read()
    if output.strip() == "":
        raise Exception
    return output.split(" ")[9:13]


if __name__ == "__main__":
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
        time.sleep(1)

        faults = open("faults.csv", "a")
        f_writer = csv.writer(faults)

        stream = os.popen('pidof gimp')
        gimp_pid = stream.read()
        gimp_pid = gimp_pid.replace("\n", "")
        if not gimp_pid: continue

        pids_to_track.add((gimp_pid, gimp_pid))

        child_pids = set()
        for pid_entry in pids_to_track:
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
            print("Counting for PID:", p[0])
            try:
                row = count_page_faults(p[0])
                if len(row) != 4: break
                #print("Found:", [gimp_pid, p[0], p[1]] + row)
                f_writer.writerow([gimp_pid, p[0], p[1], time.time_ns()] + row)
            except:
                print("FAILED")
                # PID isn't active anymore
                stopped_pids.add(p[0])
                faults.close()
                faults = open("faults.csv", "a")
                f_writer = csv.writer(faults)

    faults.close()
