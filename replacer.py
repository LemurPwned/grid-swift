import glob
import os
import re 

from tempfile import mkstemp
from shutil import move
from os import fdopen, remove
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Replace regex in file')
    parser.add_argument('root_directory', 
                        type=str, 
                        help='top-level directory to search for files')
    parser.add_argument('-f', 
                        '--file', 
                         help='filename to be searched')
    parser.add_argument('-r', 
                        '--regex', 
                        help='expression to be substituted')
    parser.add_argument('-s',
                        '--substitution',
                        help='expression to put inplace ')
    args = parser.parse_args()
    if args.root_directory is not None:
        root_path = args.root_directory
        if not os.path.isdir(root_path):
            print("Provided path is not an existing directory")
            exit(-1)
        # e.g. root_path = r'/mnt/d/Dokumenty/Simulations'
    if args.substitution is not None:
        substitution = args.substitution
    if args.file is not None or args.file != "":
        file_target = args.file
    else:
        print("No target file provided via --file")
        exit(-1)
    if args.regex is not None:
        # e.g. type_regex = '(ICHARG = )([0-9]+)'
        type_regex = args.regex
    
    infile_pattern = re.compile(type_regex)
    search_regex = os.path.join(os.path.join(root_path, '**'), file_target)
    print(search_regex)
    file_candidates = glob.iglob(search_regex, recursive=True)
    if file_candidates is None:
        print("No candidates has been found.")
        exit()
    for filename in file_candidates:
        with open(filename, 'r') as f:
            print(filename)    
            file_lines = f.read()
        x = infile_pattern.search(file_lines)
        if x is not None:
            print("BEFORE :", x.group(0))
            file_lines = file_lines.replace(x.group(0), substitution)
            x = infile_pattern.search(file_lines)
            if x is not None:
                print("AFTER: ", x.group(0))
            else: 
                print("match after substitution is empty")
            with open(filename, 'w') as f:
                f.write(file_lines)
        else:
            print("no match in file")