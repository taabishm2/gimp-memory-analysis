# import the argparse, math, and matplotlib.pyplot modules
import argparse
import math
import matplotlib.pyplot as plt

# create an ArgumentParser object
parser = argparse.ArgumentParser()

# add a positional argument for the filename
parser.add_argument('filename')
parser.add_argument('tracename')

# add an optional argument for the output filename
parser.add_argument('--output', '-o', default='histogram.png')

# parse the arguments
args = parser.parse_args()

malloc_sizes = []
trace_name = args.tracename

# open the file in read-only mode
with open(args.filename, 'r') as f:
    # iterate over each line in the file
    for line in f:
        try:
            # split the line into the two fields
            function_name, size = line.split(' ')
        except:
            #print(line)
            continue
        
        try:
            # convert the size to an integer
            size = int(size)
        except:
            #print(size)
            continue
        
        malloc_sizes.append(math.log(size))

bins = 100
hist = [0] * bins
interval_size = math.ceil(max(malloc_sizes) / bins)
for i in malloc_sizes:
    hist[int(i // interval_size)] += i

plt.bar([i for i in range(bins)], hist)

plt.ylabel('Memory')
plt.xlabel('Log(Memory)')
plt.savefig('graphs/' + 'malloc_' + trace_name + '-memmem-hist')
