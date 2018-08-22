import glob
import os
import re 

from tempfile import mkstemp
import shutil
import argparse
import subprocess

class VASPmanager:
    def __init__(self, src_dir, dst_dir=None, run=False, copy_CHGCAR=True, continuation=False):
        if copy:
            if self.dst_dir is None:
                raise ValueError("Destination directory cannnot be None")
            self.files_to_copy = ["script", "INCAR", "POTCAR", "KPOINTS"]
            if copy_CHGCAR:
                self.files_to_copy.append("CHGCAR")
            if continuation:
                # copy CONTCAR not POSCAR
                self.files_to_copy.append("CONTCAR")
                # remember to change the name later to POSCAR
                self.CONTCAR_SWAP_NAME = True
            else:
                self.files_to_copy.append("POSCAR")
        if run:
            self.find_sbatch_files(root_dir)

    def copy_wrapper(self, src, dst, follow_symlinks=True):
        file_to_copy = os.path.basename(src)
        if file_to_copy in self.files_to_copy:
            if file_to_copy == 'CONTCAR' and self.CONTCAR_SWAP_NAME:
                # remember to change the name 
                dst = os.path.join(os.path.dirname(dst), 'POSCAR')
            shutil.copy2(src, dst, follow_symlinks=follow_symlinks) 
        else:
            return 

    def copy_and_recurse_sbatch(self, src_folder, dst_folder, force=True):
        """
        copies the whole directory recursively at source down
        """
        try:
            shutil.copytree(src_folder, dst_folder, symlinks=False, copy_function=self.copy_wrapper)
        except FileExistsError:
            if force:
                # remove forcibly
                shutil.rmtree(dst_folder, ignore_errors=True)
                # retry
                self.copy_and_recurse_sbatch(src_folder, dst_folder, force=False)

    def find_sbatch_files(self, root_dir):
        sbatch_search = os.path.join(os.path.join(root_dir, '**'), "script")
        file_candidates = glob.iglob(sbatch_search, recursive=True)
        for sbatch_file in file_candidates:
            print("ENQUEUING FILE: {}".format(sbatch_file))
            self.run_simulation(sbatch_file)

    def run_simulation(self, sbatch_file):
        if os.path.isfile(sbatch_file):
            # run simulation if exists
            cmd = ["sbatch", sbatch_file]
            subprocess.Popen(cmd)

if __name__ == "__main__":
    src_folder = r'/mnt/d/Dokumenty/Simulations/Fe2Co3'
    dst_folder = r'/mnt/d/Dokumenty/Simulations/Fe2Co3_3'
    vaspM = VASPmanager(run=True, continuation=True, copy_CHGCAR=True)
    vaspM.copy_and_recurse_sbatch(src_folder, dst_folder)
    # vaspM.find_sbatch_files(dst_folder)
#     parser = argparse.ArgumentParser(description='Replace regex in file')
#     parser.add_argument('root_directory', 
#                         type=str, 
#                         help='top-level directory to search for files')
#     parser.add_argument('-f', 
#                         '--file', 
#                          help='filename to be searched')
#     parser.add_argument('-r', 
#                         '--regex', 
#                         help='expression to be substituted')
#     parser.add_argument('-s',
#                         '--substitution',
#                         help='expression to put inplace ')
#     args = parser.parse_args()
#     if args.root_directory is not None:
#         root_path = args.root_directory
#         if not os.path.isdir(root_path):
#             print("Provided path is not an existing directory")
#             exit(-1)
#         # e.g. root_path = r'/mnt/d/Dokumenty/Simulations'
#     if args.substitution is not None:
#         substitution = args.substitution
#     if args.file is not None or args.file != "":
#         file_target = args.file
#     else:
#         print("No target file provided via --file")
#         exit(-1)
#     if args.regex is not None:
#         # e.g. type_regex = '(ICHARG = )([0-9]+)'
#         type_regex = args.regex
    
#     infile_pattern = re.compile(type_regex)
#     search_regex = os.path.join(os.path.join(root_path, '**'), file_target)
#     print(search_regex)
#     file_candidates = glob.iglob(search_regex, recursive=True)
#     if file_candidates is None:
#         print("No candidates has been found.")
#         exit()
#     for filename in file_candidates:
#         with open(filename, 'r') as f:
#             print(filename)    
#             file_lines = f.read()
#         x = infile_pattern.search(file_lines)
#         if x is not None:
#             print("BEFORE :", x.group(0))
#             file_lines = file_lines.replace(x.group(0), substitution)
#             x = infile_pattern.search(file_lines)
#             if x is not None:
#                 print("AFTER: ", x.group(0))
#             else: 
#                 print("match after substitution is empty")
#             with open(filename, 'w') as f:
#                 f.write(file_lines)
#         else:
#             print("no match in file")