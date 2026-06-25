
import QuickLook as quicklook

def fn_generator(date, head, start, end, mode):
    obsnum_strings = [f"{i:05d}" for i in range(start, end + 1)]
    fns = []
    for string in obsnum_strings:
        fn = date+'_'+head+'_'+mode+'_'+string+'.fits'
        fns.append(fn)

    return fns

path= '/Volumes/wd/SCALES/UCSC_data/CD4/20260209/'

head = 'Im'
date = '20260209'
obsnum_start = 960
obsnum_end = 1036

fns = fn_generator(date, head, obsnum_start, obsnum_end, 'UTR')

for filename in fns:
    quicklook.run_quicklook(path+filename,iswrite=True) 
#iswrite=False if you don't need corrected cube of reads
