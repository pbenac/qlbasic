
import QuickLook as quicklook
import os
import numpy as np



def prefix_for_head(head):
    return "ss" if head == "IFS" else "si"


def fits_path(datapath, head, date, filenum):
    obsnum_string = f"{int(filenum):05d}"
    filename = prefix_for_head(head) + date + "_" + obsnum_string + ".fits"
    return os.path.join(datapath, filename)

read_path= '/data20/CD5/IMG/jun23/'
write_path = '/home/pbenac/CD5_fitsfiles/'

date='260623'
head = 'Im'
first = 4359
last = 4550
nums = np.linspace(first,last,num=(last-first)+1).astype(int)

fns = []
for num in nums:
    fns.append(fits_path(read_path, head, date, num))

for filename in fns:
    quicklook.run_quicklook(filename, output_dir=write_path, iswrite=True) 
#iswrite=False if you don't need corrected cube of reads
