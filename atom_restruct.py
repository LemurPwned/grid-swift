import re
import numpy as np
from functools import reduce


class AtomRestruct:
    def __init__(self):
        self.regex = '\W+'
        self.lattice_subregex = r'(-?\s+[0-9]+\.?[0-9]+)(-?\s+[0-9]+\.?[0-9]+)(-?\s+[0-9]+\.?[0-9]+)'
    def read_poscar(self, filename):
        poscar_data = {}
        with open(filename, 'r') as f:
            poscar_data['name'] = re.sub(self.regex, '',f.readline())
            poscar_data['scaler'] = float(f.readline())
            poscar_data['lattice'] = self.parse_translation_matrix(
               [next(f) for i in range(3)]) # basis vectors
            poscar_data['conf'] = self.extract_conf_num(
               [next(f) for i in range(2)])
            poscar_data['coord_type'] = re.sub(self.regex, '', f.readline())
            x = f.readline()
            atom_struct = []
            print(poscar_data['conf'])
            poscar_data['atom_num'] = reduce(lambda x, y: ('num', x[1]+ y[1]),
                                             poscar_data['conf'])[1]
            for i in range(poscar_data['atom_num']):
                atom_struct.append(self.parse_coords(x,
                                                     poscar_data['coord_type'],
                                                     poscar_data['lattice'],
                                                     poscar_data['scaler']))
                x = f.readline()
        atom_struct = np.array(atom_struct)
        try:
            assert atom_struct.shape == (poscar_data['atom_num'], 3)
        except AssertionError:
            print("Invalid lattice shape: found {}, expected {}".format(
            atom_struct.shape, (poscar_data['atom_num'], 3)
            ))
        poscar_data['lattice_vectors'] = atom_struct
        return poscar_data

    def parse_coords(self, coords, coords_type, lattice_matrix, lattice_scaler):
        match = re.search(self.lattice_subregex, coords)
        try:
            fin_coord = np.array([float(match.group(i))
                                  for i in range(1,4)])*lattice_scaler
        except ValueError:
            raise ValueError("Invalid lattice vector {}".format(coords))
        return np.dot(lattice_matrix, fin_coord)

    def extract_conf_num(self, header):
        return [(atom, int(num)) for atom, num in zip(
            re.sub(self.regex, '\b',header[0]).split('\b'),
            re.sub(self.regex, '\b',header[1]).split('\b'))
        if atom != '']

    def parse_translation_matrix(self, header):
        matrix = []
        for line in header:
            row = []
            for entry in line.split(' '):
                try:
                    row.append(float(entry))
                except ValueError:
                    pass # failed to parse to float
            matrix.append(row)
        return matrix


if __name__ == "__main__":
    ar = AtomRestruct()
    ar.read_poscar("POSCAR")
