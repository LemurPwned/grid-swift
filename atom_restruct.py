import re
import sys
import numpy as np
from functools import reduce
from colorama import Fore, Style

class AtomRestruct:
    def __init__(self):
        self.regex = '\W+'
        self.lattice_subregex = r'(-?\s+[0-9]+\.?[0-9]+)(-?\s+[0-9]+\.?[0-9]+)(-?\s+[0-9]+\.?[0-9]+)'

    def save_poscar(self, filename, poscar):
        with open(filename, 'w') as f:
            f.write(poscar['name'] + '\n')
            f.write('  ' + str(poscar['scaler']) + '\n')
            for row in poscar['lattice']:
                print('    ', file=f, end='')
                print(*row, sep=', ', file=f, end='')
                print('\n', file=f, end='')
            a_str = "  "
            b_str = "    "
            for el in poscar['conf']:
                a_str += str(el[0]) + '  '
                b_str += str(el[1]) + '   '
            f.write(a_str + '\n')
            f.write(b_str + '\n')
            f.write('Cartesian\n')
            for pos in poscar['restruct_lattice']:
                print('  ', file=f, end='')
                print(*pos[0], sep=', ', file=f, end='')
                print('\n', file=f, end='')

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
            poscar_data['atom_order'] = [pair[0]
                                         for pair in poscar_data['conf']
                                         for i in range(pair[1])]
            poscar_data['atom_num'] = reduce(lambda x, y: ('num', x[1]+ y[1]),
                                             poscar_data['conf'])[1]
            for i in range(poscar_data['atom_num']):
                coord = self.parse_coords(x, poscar_data['coord_type'],
                                          poscar_data['lattice'],
                                          poscar_data['scaler'])
                atom_struct.append(coord)
                x = f.readline()
        try:
            assert len(atom_struct) == poscar_data['atom_num']
        except AssertionError:
            print("Invalid lattice shape: found {}, expected {}".format(
            len(atom_struct), (poscar_data['atom_num'], 3)
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

    def lattice_positons(self, positions, symbols, axis=-1):
        lattice = [(atom_pos, atom_sym)
                   for atom_pos, atom_sym in zip(positions, symbols)]
        lattice.sort(key=lambda pair: pair[0][axis])
        self.print_lattice(lattice)
        pos = int(input("Insert number: "))
        sym = input("Atom symbol: ")
        if pos > len(positions) or pos < 0:
            raise ValueError("Position out of range")
        elif sym not in symbols:
            raise ValueError("Symbol not found in symbols")
        else:
            print("Insering atom {} in place {}".format(sym, pos))
        if pos == 0:
            prev_bond = None
            next_bond = positions[pos+1]
        elif pos == len(positions):
            prev_bond, next_bond = positions[pos-1], None
        else:
            prev_bond, next_bond = lattice[pos-1][0], lattice[pos][0]
            prev_sym, next_sym = lattice[pos-1][1], lattice[pos][1]
            # new position is at pos
            prev_b = self.find_bond_length([prev_sym, sym],lattice)
            next_b = self.find_bond_length([sym, next_sym],lattice)
            print(prev_b, next_b)
            x = float(input("Enter x coordinate: "))
            y = float(input("Enter y coordinate: "))
            new_pos = [x, y, prev_bond[2]-prev_b[2]]
            # shift all remaining by a vector in z
            # z pos of next atom = bond_length + z pos of inserted
            # thus z shift is old_pos - new _z pos
            znext = new_pos[2] - next_b[2]
            zshift = next_bond[2]-znext if next_bond[2]>znext else znext-next_bond[2]
            print(znext, zshift, next_b[2], new_pos[2], next_bond[2])
            lattice.insert(pos, (new_pos, sym))
            lattice[pos+1:] = map(lambda x: ([*x[0][:2],x[0][2]+zshift], x[1]),
                                lattice[pos+1:])
            self.print_lattice(lattice, pos)
            return lattice

    def print_lattice(self, lattice,  index_highlight=None):
        for i, atom in enumerate(lattice):
            if i == index_highlight:
                print(Fore.GREEN + "{}. {} in {}".format(i, atom[1], atom[0]) + Style.RESET_ALL)
            else:
                print("{}. {} in {}".format(i, atom[1], atom[0]))

    def find_bond_length(self, bond_type, atom_sym_pairs):
        print("Looking for {}-{}".format(bond_type[0], bond_type[1]))
        for i, pair in enumerate(atom_sym_pairs):
            for j in range(2):
                if pair[1] == bond_type[j]:
                    try:
                        print(pair[1], atom_sym_pairs[i+1][1])
                        if atom_sym_pairs[i+1][1] == bond_type[j^1]:
                            # found the bond
                            return pair[0]-atom_sym_pairs[i+1][0]
                    except IndexError:
                        # insert boundary condition check here
                        pass

if __name__ == "__main__":
    print(sys.argv)
    ar = AtomRestruct()
    poscar = ar.read_poscar("POSCAR")
    new_lattice = ar.lattice_positons(poscar['lattice_vectors'],
                                   poscar['atom_order'])
    poscar['restruct_lattice'] = new_lattice
    ar.save_poscar('test', poscar)

