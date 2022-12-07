import os
import csv
import time

def count_page_faults(pid):
    pid = pid.replace('\n','')
    stream = os.popen('cat /proc/' + pid + '/stat')
    output = stream.read()
    if len(output) == 0 or len(output.split(" ")) < 14:
        return []
    return output.split(" ")[9:13]


if __name__ == "__main__":
    faults = open("faults.csv", "w")
    f_writer = csv.writer(faults)
    f_writer.writerow(['pid', 'minflt', 'cminflt', 'majflt', 'cmajflt'])
    faults.close()
    while True:
        print("Searching...")
        time.sleep(1)
        faults = open("faults.csv", "w")
        f_writer = csv.writer(faults)

        stream = os.popen('pidof gimp')
        pid = stream.read()
        pid = pid.replace("\n", "")
        if not pid: continue

        try:
            row = count_page_faults(pid)
            if len(row) != 4: break
            print("Found:", [pid] + row)
            f_writer.writerow(pid + row)
        except:
            faults.close()

    faults.close()
