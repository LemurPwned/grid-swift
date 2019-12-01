import argparse
import csv
import glob
import json
import os
import re
import shutil
import subprocess
from itertools import combinations, repeat
from tempfile import mkstemp

import numpy as np
import pandas as pd

from Interface import Interface, ParsingStage

required_arguments = {
    "ions": ["ion_config"],
    "analyze": [],
    "copy": ["src_dir", "dst_dir", "copy_CHGCAR", "cont"],
    "replace": ["dst_dir"],
    "run": ["dst_dir"]
}


class VASPmanager:
    def __init__(self, filename=None):
        self.dst_dir = None
        self.src_dir = None
        if filename:
            specification = self.extract_arguments_from_json(filename)
            self.set_inner_interface_specification(specification)
            self.set_parameters(**self.startup_dict)

            try:
                self.check_required_arguments('analyze')
                if (self.analyze is not None) and (len(self.analyze) == 2):
                    print(self.analyze)
                    self.calculate_free_energy(self.analyze)
                    quit()
            except AttributeError as e:
                print(e)
                pass
            try:
                self.check_required_arguments('ions')
                if (len(self.ions) == 2) and (self.ion_config is not None):
                    print(self.ions)
                    conf = json.load(open(self.ion_config, 'r'))
                    self.ion_compare(self.ions, conf)
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
                self.copy_and_recurse_sbatch(self.src_dir,
                                             self.dst_dir,
                                             force=True)
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
        s1_i = len(string1) - 1
        s2_i = len(string2) - 1
        while string1[s1_i] == string2[s2_i]:
            s1_i -= 1
            s2_i -= 1
            if s1_i < 0 or s2_i < 0:
                break
        if s1_i == 0:
            return string1
        return string1[s1_i + 1:]

    def compose_ions(self, ions):
        result_list = []
        assert len(ions) % 2 == 0
        ions_per_state = int(len(ions) / 2)  # assume there are 2 states
        for i in range(ions_per_state):
            result_list.append(ions[i] - ions[ions_per_state + i])
        result_list.append(
            np.sum(ions[:ions_per_state] - np.sum(ions[ions_per_state:])))
        return result_list

    def ion_compare(self, root_dirs, config_file):
        diff_list = []
        states = 2
        # above assumes there is an equal number of ions in the file
        for ion_folder in config_file['ions']:
            # find folder
            e = []
            for i, folder in enumerate(root_dirs):
                outcar_file = os.path.join(root_dirs[i], ion_folder['folder'],
                                           'OUTCAR')
                for atom in ion_folder['atoms']:
                    # extract each atom for each file
                    e.append(self.get_ion_energy(outcar_file, atom))
            diff_list.append([ion_folder['folder'], *e, *self.compose_ions(e)])
            names_list = [
                f"state1_ion{i}_state2_ion{i}"
                for i in range(len(config_file['ions'][0]['atoms']))
            ]
        names_list.append("sum(state1)-sum(state2)")
        names_list = [
            "filename", *[
                f"state{j}_ion{i}" for j in range(states)
                for i in range(len(config_file['ions'][0]['atoms']))
            ]
        ] + names_list
        if root_dirs[0][-1] != '/':
            root_dirs[0] += '/'
        if root_dirs[1][-1] != '/':
            root_dirs[1] += '/'
        savepoint_ = os.path.join(
            os.path.commonpath(root_dirs),
            f'{os.path.split(os.path.dirname(root_dirs[0]))[-1]}_vs_{os.path.split(os.path.dirname(root_dirs[1]))[-1]}_ion_compare.csv'
        )
        print(f"Saving in {savepoint_}")
        with open(savepoint_, 'w') as f:
            csv_writer_root_file = csv.writer(f,
                                              delimiter=',',
                                              lineterminator='\n')
            csv_writer_root_file.writerow(names_list)
            csv_writer_root_file.writerows(diff_list)

    def get_ion_energy(self, filename, ion_number):
        """
        :param filename
        :param ion_number int or an array
        Open the OUTCAR and find the ion energy
        """
        if type(ion_number) is list:
            ion_number = [str(i) for i in ion_number]
            # we have a list of ions to find
            matched_ions = '[' + ''.join(ion_number) + ']'
        else:
            matched_ions = ion_number
        regex_str = f'(Ion:\s+)({matched_ions})(\s+E_soc:\s+)(-?[0-9]?.?[0-9]+)'
        regex = re.compile(regex_str)
        ion_energies = {}
        with open(filename, 'r') as f:
            for line in f:
                m = re.search(regex, line)
                if m is not None:
                    ion_energy = float(m.group(4))
                    ion_num = int(m.group(2))
                    ion_energies[str(ion_num)] = ion_energy
        if type(ion_number) is int:
            assert len(list(ion_energies.keys())) == 1
            return ion_energy
        else:
            return ion_energies

    def get_ion_positions(self, poscar_file):
        """
        Extract the position of the FM atoms
        - look for Co, Fe
        """
        # Read the poscar
        precise_positions = {}
        with open(poscar_file) as fp:
            for i, line in enumerate(fp):
                if i == 5:
                    # read the atoms
                    atoms = line.strip().split(' ')
                    atoms = [atom.strip() for atom in atoms if atom]
                    # the positions I need are only for Co and Fe
                if i == 6:
                    atom_nums = line.strip().split(' ')
                    atom_nums = [
                        int(atom.strip()) for atom in atom_nums if atom
                    ]
                    assert len(atom_nums) == len(atoms)
                    atoms_repeated = []
                    for atom_name, k in zip(atoms, atom_nums):
                        for atm in repeat(atom_name, k):
                            atoms_repeated.append(atm)
                    atoms_pos = {}
                    for atom_i, atom_name in enumerate(atoms_repeated):
                        if ('Co' in atom_name) or ('Fe' in atom_name):
                            atoms_pos[atom_i + 1] = atom_name
                elif i >= 8:
                    # i + 1, start from 1
                    true_i = i - 7
                    if true_i in atoms_pos:
                        precise_pos = line.strip().split(' ')
                        precise_pos = [float(p) for p in precise_pos if p]
                        # map atom position to
                        precise_positions[str(true_i)] = (precise_pos, atoms_pos[true_i])
        return precise_positions

    def extract_vcma_energies(self, root_dir, ions=[1, 2, 3, 4, 5]):
        """
        Extracts the VCMA energies from given MLs.
        Assumes ML is a single atom.
        For each filename we extract full info:
        - All ions creating FM ML layers
        - Their positions and energies
        """
        ion_map = {
            'folder': [],
            'ion_energy': [],
            'ion_id': [],
            'ion_position_x': [],
            'ion_position_y': [],
            'ion_position_z': [],
            'ion_type': []
        }
        flat_root = glob.glob(os.path.join(root_dir, '*/*/OUTCAR'))
        for base_folder in flat_root:
            base = os.path.dirname(base_folder)
            # find folder
            outcar_file = os.path.join(base, 'OUTCAR')
            ion_energies = self.get_ion_energy(outcar_file, ions)
            poscar_file = os.path.join(base, 'POSCAR')
            ion_positions = self.get_ion_positions(poscar_file)
            assert len(ion_positions) == len(ion_energies) == len(ions)
            # print(ion_energies)
            # print(ion_positions)
            base = base.replace(root_dir,'')
            for ion_no in ions:
                ion_map['folder'].append(base)
                ion_map['ion_energy'].append(ion_energies[str(ion_no)])
                ion_pos, ion_type  = ion_positions[str(ion_no)]
                ion_map['ion_id'].append(ion_no)
                ion_map['ion_position_x'].append(ion_pos[0])
                ion_map['ion_position_y'].append(ion_pos[1])
                ion_map['ion_position_z'].append(ion_pos[2])

                ion_map['ion_type'].append(ion_type)
        df = pd.DataFrame.from_dict(ion_map)
        return df 

    def calculate_free_energy(self, root_dirs):
        regex = re.compile(
            '(F=\s+)(-?\.?[0-9]+E?\-?\+?[0-9]*\s+)(E0=\s+)(-?\.?[0-9]+E?\-?\+?[0-9]*\s+)'
        )
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
                            f"Problem with file {filepath}, skipping pair {file_pair}"
                        )
                        break
                    m = re.search(regex, p)
                    if m is not None:
                        vals.append(float(m.group(2)))  # F
                        vals.append(float(m.group(4)))  # E
            try:
                result_list.append([
                    os.path.dirname(file_pair), vals[0], vals[2],
                    vals[0] - vals[2], vals[1], vals[3], vals[1] - vals[3]
                ])
            except IndexError:
                pass
        cols = ['filename', 'pF', 'pE', 'aF', 'aE', 'DF', 'DE']
        if root_dirs[0][-1] != '/':
            root_dirs[0] += '/'
        if root_dirs[1][-1] != '/':
            root_dirs[1] += '/'
        savepoint_ = os.path.join(
            os.path.commonpath(root_dirs),
            f'{os.path.split(os.path.dirname(root_dirs[0]))[-1]}_vs_{os.path.split(os.path.dirname(root_dirs[1]))[-1]}_res.csv'
        )
        print(f"Saving in {savepoint_}")
        result_list = np.array(result_list)
        result_list = result_list[result_list[:, 0].argsort()]
        with open(savepoint_, 'w') as f:
            csv_writer_root_file = csv.writer(f,
                                              delimiter=',',
                                              lineterminator='\n')
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
            shutil.copytree(src_folder,
                            dst_folder,
                            symlinks=False,
                            copy_function=self.copy_wrapper)
        except FileExistsError:
            if force:
                # remove forcibly
                print("DIRECTORY EXISTS: {}, REMOVING".format(dst_folder))
                shutil.rmtree(dst_folder, ignore_errors=True)
                # retry
                self.copy_and_recurse_sbatch(src_folder,
                                             dst_folder,
                                             force=False)
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

    def check_required_arguments(self, arg_name):
        for dependency in required_arguments[arg_name]:
            try:
                getattr(self, dependency)
            except AttributeError:
                print(
                    f"Used {arg_name} following argument is required: {dependency}"
                )


if __name__ == "__main__":
    # vaspM = VASPmanager("config/interface.json")
    vaspM = VASPmanager(None)
    root_dir = '/Users/jakubmojsiejuk/Documents/agh/ab-initio/charge-relax-v0-inplane'
    df = vaspM.extract_vcma_energies(root_dir)
    df.to_csv('test.csv')
