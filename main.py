
import gc, os, sys, glob, argparse, utils
import subprocess
from openephys2nwb import save_nwb
import shutil


if __name__ == "__main__":

    p = argparse.ArgumentParser(description=\
    'Convert open ephys directory to the Neurodata Without Borders file format')

    p.add_argument('--source', type=str , dest = 'source_dir', help='source')
    p.add_argument('--destination', type=str , dest = 'dest_dir', help='destination')

    args = p.parse_args(); src = str(args.source_dir); dst = str(args.dest_dir)

    save_nwb(src, dst)



