import glob
import os
import re
import csv
from tempfile import mkstemp
import shutil
import argparse
import subprocess
import json
import numpy as np
from Interface import Interface, ParsingStage


class VASPmanager:
    def __init__(self, filename):
        self.dst_dir = None
        self.src_dir = None
        specification = self.extract_arguments_from_json(filename)
        self.set_inner_interface_specification(specification)
        self.set_parameters(**self.startup_dict)

        try:
            if (self.analyze is not None) and (len(self.analyze) == 2):
                print(self.analyze)
                self.calculate_free_energy(self.analyze)
                quit()
        except AttributeError as e:
            print(e)
            pass
        if self.copy:
            self.check_dst_dir()
            if self.src_dir is None:
                raise ValueError("Source directory cannot by None")
            self.files_to_copy = ["script", "INCAR", "POTCAR", "KPOINTS"]
            if self.copy_CHGCAR:
                self.files_to_copy.append("CHGCAR")
            if self.cont:
                # copy CONTCAR not POSCAR
                self.files_to_copy.append("CONTCAR")
                # remember to change the name later to POSCAR
                self.CONTCAR_SWAP_NAME = True
            else:
                self.files_to_copy.append("POSCAR")
            print("COPYING FILES {} from {} to {}".format(
                self.files_to_copy, self.src_dir, self.dst_dir))
            self.copy_and_recurse_sbatch(
                self.src_dir, self.dst_dir, force=True)
        if self.replace:
            self.check_dst_dir()
            for filename, regex, substitution in self.replacements:
                print("CURRENTLY REPLACING {} for {} in files: {}".format(
                    regex, substitution, filename))
                self.replacer(self.dst_dir, filename, regex, substitution)
        if self.run:
            self.check_dst_dir()
            self.find_sbatch_files(self.dst_dir)

    def check_dst_dir(self):
        if self.dst_dir is None:
            raise ValueError("Destination directory cannnot be None")

    def set_parameters(self, **kwargs):
        """
        :param: **kwargs are the arguments to be passed to the main widget
        iterator
        """
        for k, v in kwargs.items():
            setattr(self, k, v)

    def match_paths(self, paths):
        matching_paths = []
        for path in paths[0]:
            longest_match_len = 0
            current_match = None
            for second_path in paths[1]:
                match = self.find_common_substring(path, second_path)
                if len(match) > longest_match_len:
                    longest_match_len = len(match)
                    current_match = match
            if current_match == None:
                raise ValueError("File has not been matched")
            else:
                matching_paths.append(current_match)
        return matching_paths

    def find_common_substring(self, string1, string2):
        s1_i = len(string1)-1
        s2_i = len(string2)-1
        while string1[s1_i] == string2[s2_i]:
            s1_i -= 1
            s2_i -= 1
            if s1_i < 0 or s2_i < 0:
                break
        if s1_i == 0:
            return string1
        return string1[s1_i+1:]

    def calculate_free_energy(self, root_dirs):
        regex = re.compile(
            '(F=\s+)(-?\.?[0-9]+E?\-?\+?[0-9]*\s+)(E0=\s+)(-?\.?[0-9]+E?\-?\+?[0-9]*\s+)')
        res_list = []
        oszicar_search = os.path.join(root_dirs[0], '**', 'OSZICAR')
        p_file_search = glob.glob(oszicar_search, recursive=True)
        oszicar_search = os.path.join(root_dirs[1], '**', 'OSZICAR')
        ap_file_search = glob.glob(oszicar_search, recursive=True)
        assert len(p_file_search) > 0
        assert len(p_file_search) == len(ap_file_search)
        matches = self.match_paths((p_file_search, ap_file_search))
        result_list = []
        for file_pair in matches:
            current_row = []
            vals = []
            for i in range(2):
                if file_pair[0] == '/':
                    file_pair = file_pair[1:]
                filepath = os.path.join(root_dirs[i], file_pair)
                with open(filepath, 'r') as f:
                    x = f.readlines()  # ineffective, change later
                    try:
                        p = x[-1]
                    except IndexError:
                        print(
                            f"Problem with file {filename}, skipping pair {file_pair}")
                        break
                    m = re.search(regex, p)
                    if m is not None:
                        vals.append(float(m.group(2)))  # F
                        vals.append(float(m.group(4)))  # E
            try:
                result_list.append([os.path.dirname(file_pair), vals[0], vals[2], vals[0]-vals[2], vals[1], vals[3], vals[1]-vals[3]])
            except IndexError:
                pass
        cols = ['filename', 'pF', 'pE', 'aF', 'aE', 'DF', 'DE']
        if root_dirs[0][-1] != '/':
           root_dirs[0] += '/'
        if root_dirs[1][-1] != '/':
           root_dirs[1] += '/'
        savepoint_ = os.path.join(os.path.commonpath(root_dirs),
                                  f'{os.path.split(os.path.dirname(root_dirs[0]))[-1]}_vs_{os.path.split(os.path.dirname(root_dirs[1]))[-1]}_res.csv')
        print(f"Saving in {savepoint_}")
        result_list = np.array(result_list)
        result_list = result_list[result_list[:, 0].argsort()]
        with open(savepoint_, 'w') as f:
            csv_writer_root_file = csv.writer(
                f, delimiter=',', lineterminator='\n')
            csv_writer_root_file.writerow(cols)
            csv_writer_root_file.writerows(result_list)

    def extract_arguments_from_json(self, filepath):
        with open(filepath, 'r') as f:
            spec = json.loads(f.read())
        return spec

    def set_inner_interface_specification(self, specification):
        inner_interface = Interface(specification)
        ps = ParsingStage(inner_interface)
        self.startup_dict = ps.resultant_dict
        if self.startup_dict is None:
            raise ValueError("No arguments specified")

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
            shutil.copytree(src_folder, dst_folder, symlinks=False,
                            copy_function=self.copy_wrapper)
        except FileExistsError:
            if force:
                # remove forcibly
                print("DIRECTORY EXISTS: {}, REMOVING".format(dst_folder))
                shutil.rmtree(dst_folder, ignore_errors=True)
                # retry
                self.copy_and_recurse_sbatch(
                    src_folder, dst_folder, force=False)
            else:
                print("DIRECTORY EXISTS: {}, SKIPPING".format(dst_folder))
                pass

    def find_sbatch_files(self, root_dir):
        sbatch_search = os.path.join(os.path.join(root_dir, '**'), "script")
        file_candidates = glob.iglob(sbatch_search, recursive=True)
        for sbatch_file in file_candidates:
            print("ENQUEUING FILE: {}".format(sbatch_file))
            self.run_simulation(sbatch_file)

    def run_simulation(self, sbatch_file):
        if os.path.isfile(sbatch_file):
            # run simulation if exists
            os.chdir(os.path.dirname(sbatch_file))
            cmd = ["sbatch", os.path.basename(sbatch_file)]
            subprocess.Popen(cmd)

    def replacer(self, root_path, file_target, type_regex, substitution):
        infile_pattern = re.compile(type_regex)
        search_regex = os.path.join(os.path.join(root_path, '**'), file_target)
        print(search_regex)
        file_candidates = glob.iglob(search_regex, recursive=True)
        print(file_candidates)
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


if __name__ == "__main__":
    vaspM = VASPmanager("config/interface.json")
