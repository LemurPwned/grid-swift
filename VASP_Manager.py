import glob
import os
import re
import csv
from tempfile import mkstemp
import shutil
import argparse
import subprocess
import json

from Interface import Interface, ParsingStage


class VASPmanager:
    def __init__(self, filename):
        self.dst_dir = None
        self.src_dir = None
        specification = self.extract_arguments_from_json(filename)
        self.set_inner_interface_specification(specification)
        self.set_parameters(**self.startup_dict)

        if self.analyze:
            self.check_dst_dir()
            self.calculate_free_energy(self.dst_dir)
            quit()
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

    def calculate_free_energy(self, root_dir):
        regex = re.compile(
            '(F=\s+)(-?\.?[0-9]+E?\-?\+?[0-9]*\s+)(E0=\s+)(-?\.?[0-9]+E?\-?\+?[0-9]*\s+)')

        csv_writer_root_file = csv.writer(
            open(f'{os.path.basename(root_dir)}_res.csv', 'wb'), delimiter=';')
        res_list = []
        dict_res = {}
        for subfolder in ['p', 'ap']:
            dict_res[subfolder]['F'] = []
            dict_res[subfolder]['E'] = []
            dict_res[subfolder]['filename']
            subfolder_path = os.path.join(root_dir, subfolder)
            slurm_out_serach = os.path.join(
                os.path.join(subfolder_path, '**'), "slurm*.out")
            file_candidates = glob.iglob(slurm_out_serach, recursive=True)
            if file_candidates is None:
                raise ValueError(f"No results found in subfolder {subfolder}")
            for filename in file_candidates:
                with open(filename, 'r') as f:
                    p = subprocess.check_output(
                        ['tail', '-n', '10', filename])
                    p = p.decode("utf-8").split('\\n')
                    for el in p:
                        m = re.search(regex, el)
                        if m is not None:
                            print(m.group(2), m.group(4))
                            dict_res[subfolder]['F'].append(float(m.group(2)))
                            dict_res[subfolder]['E'].append(float(m.group(4)))
                            dict_res[subfolder]['filename'].append(
                                os.path.basename(filename))

            DE = [eap - ep for ep, eap in zip(
                dict_res['p']['E'], dict_keys['ap']['E'])]
            DF = [fap - fp for fp, fap in zip(
                dict_res['p']['F'], dict_keys['ap']['F'])]

        cols = ['filename', 'F', 'E', 'DF', 'DE']
        csv_writer_root_file.writerow(cols)
        csv_writer_root_file.writerows(dict_res['p']['filename'], dict_res['p']['E'], dict_res['ap']['E'], DE,
                                       dict_res['p']['F'], dict_res['ap']['F'], DF)

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
