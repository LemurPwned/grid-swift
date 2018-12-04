import re
import sys
import argparse
import numpy as np
from functools import reduce

class AtomRestruct:
    def __init__(self):
        self.regex = '\W+'
        self.lattice_subregex = '(-?[0-9]+\.?[0-9]+e?-?[0-9]*)'
        self.print_lattice = self.print_lattice_space

    def save_poscar(self, filename, poscar):
        # group lattice
        poscar['restruct_lattice'].sort(key=lambda pair: pair[1])
        conf = {}
        for _, sym in poscar['restruct_lattice']:
            if sym in conf:
                conf[sym] +=1
            else:
                conf[sym] = 1
        with open(filename, 'w') as f:
            f.write(poscar['name'] + '\n')
            f.write(f"      {str(poscar['scaler'])}\n")
            for row in poscar['basis']:
                print('    ', file=f, end='')
                print(*row, sep='  ', file=f, end='')
                print('\n', file=f, end='')
            a_str = "  "
            b_str = "    "
            for key in conf:
                a_str += str(key) + '  '
                b_str += str(conf[key]) + '   '
            f.write(a_str + '\n')
            f.write(b_str + '\n')
            f.write('Cartesian\n')
            for pos in poscar['restruct_lattice']:
                print('  ', file=f, end='')
                print(*pos[0], sep='  ', file=f, end='')
                print('\n', file=f, end='')

    def read_poscar(self, filename):
        poscar_data = {}
        with open(filename, 'r') as f:
            poscar_data['name'] = re.sub(self.regex, '',f.readline())
            poscar_data['scaler'] = float(f.readline())
            poscar_data['basis'] = self.parse_translation_matrix(
               [next(f) for i in range(3)]) # basis vectors
            poscar_data['conf'] = self.extract_conf_num(
               [next(f) for i in range(2)])
            x = f.readline()
            if (x.strip() != 'Direct') and (x.strip()!='Cartesian'):
                x = f.readline()
            poscar_data['coord_type'] = re.sub(self.regex, '', x)
            atom_struct = []
            print(poscar_data)
            poscar_data['atom_order'] = [pair[0]
                                         for pair in poscar_data['conf']
                                         for i in range(pair[1])]
            poscar_data['atom_num'] = reduce(lambda x, y: ('num', x[1]+ y[1]),
                                             poscar_data['conf'])[1]
            x = f.readline()
            for i in range(poscar_data['atom_num']):
                coord = self.parse_coords(x, poscar_data['coord_type'],
                                          poscar_data['basis'],
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
        match = re.findall(self.lattice_subregex, coords)
        try:
            fin_coord = np.array([float(i)
                                  for i in match])*lattice_scaler
            if (fin_coord is None) or (len(fin_coord) == 0):
                raise ValueError
        except ValueError:
            raise ValueError(f"Invalid lattice vector {coords}")
        try:
           return np.dot(lattice_matrix, fin_coord)
        except ValueError:
            print(f"Invalid dot {fin_coord}")

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

    def lattice_positions(self, poscar, infer, axis=-1):
        positions = poscar['lattice_vectors']
        symbols = poscar['atom_order']
        lattice = [(atom_pos, atom_sym)
                   for atom_pos, atom_sym in zip(positions,
                                                 symbols)]
        lattice.sort(key=lambda pair: pair[0][axis])
        self.print_lattice(lattice)
        pos = int(input("Insert position: "))
        sym = input("Atom symbol: ")
        x = float(input("Enter x coordinate: "))
        y = float(input("Enter y coordinate: "))
        if pos > len(positions) or pos < 0:
            raise ValueError("Position out of range")
        elif sym not in symbols:
            raise ValueError("Symbol not found in symbols")
        else:
            print(f"Inserting atom {sym} in place {pos}")
        if pos == len(positions):
            prev_bond, next_bond = lattice[pos-1][0], None
            prev_sym, next_sym = lattice[pos-1][1], None
            # insert at the end, so no shifting
            prev_b = self.find_bond_length([prev_sym, sym],lattice)
            new_pos = [x, y, prev_bond[2]-prev_b[2]]
            lattice.insert(pos, (new_pos, sym))
        else:
            prev_bond, next_bond = lattice[pos-1][0], lattice[pos][0]
            prev_sym, next_sym = lattice[pos-1][1], lattice[pos][1]
            # new position is at pos
            prev_b = self.find_bond_length([prev_sym, sym],lattice)
            next_b = self.find_bond_length([sym, next_sym],lattice)
            if infer:
                bond_shift = self.preserve_structure(pos, [prev_sym, sym],
                                                     lattice)
                new_pos = [*bond_shift[:2], prev_bond[2]-prev_b[2]]
            else:
                new_pos = [x, y, prev_bond[2]-prev_b[2]]
            if pos == 0:
                new_pos = [x, y, np.abs(prev_b[2])]
            # shift all remaining by a vector in z
            # z pos of next atom = bond_length + z pos of inserted
            # thus z shift is old_pos - new _z pos
            znext = new_pos[2] - next_b[2]
            zshift = next_bond[2]-znext if next_bond[2]>znext else znext-next_bond[2]
            print(znext, zshift, next_b[2], new_pos[2], next_bond[2])
            lattice.insert(pos, (new_pos, sym))
            lattice[pos+1:] = map(lambda x: ([*x[0][:2],x[0][2]+zshift], x[1]),
                                lattice[pos+1:])
        self.print_lattice(lattice, index_highlight=pos)
        # update maximum zshift
        poscar['basis'][2][2] = poscar['basis'][2][2] + zshift
        poscar['conf'] = map(lambda x: (x[0], x[1]+1) if x[0]==sym else x,
                                  poscar['conf'])
        poscar['restruct_lattice'] = lattice
        return poscar

    def print_lattice_space(self, lattice, axis=1, index_highlight=-1):
        if type(index_highlight) == list:
            index_highlight = [i for i in
                               range(index_highlight[0],
                                     index_highlight[1])]
        else:
            index_highlight = [index_highlight]
        # sort the lattice in the plane
        # find unique lattice in [1] axis
        positions = np.array(list(map(lambda x: x[0], lattice)))
        unique_plane = np.unique(positions[:,axis])
        unique_plane.sort()
        spacing = {unique_plane[i]: ' '*i
                   for i in range(len(unique_plane))}
        c = 0
        for pos, atm in lattice:
            if c in index_highlight:
                print(f"\033[32m{c}.{spacing[pos[axis]]}{atm}\033[0m")
            else:
                print(f"{c}.{spacing[pos[axis]]}{atm}")
            c += 1

    def print_lattice_flat(self, lattice,  index_highlight=-1):
        if type(index_highlight) == list:
            index_highlight = [i for i in
                               range(index_highlight[0],
                                     index_highlight[1])]
        else:
            index_highlight = [index_highlight]

        for i, atom in enumerate(lattice):
            if i in index_highlight:
                print(f"\033[32m{i}. {atom[1]} in {atom[0]}\033[0m")
            else:
                print(f"{i}. {atom[1]} in {atom[0]}")

    def find_bond_length(self, bond_type, atom_sym_pairs):
        print(f"Looking for {bond_type[0]}-{bond_type[1]}")
        for i, pair in enumerate(atom_sym_pairs):
            for j in range(2):
                if pair[1] == bond_type[j]:
                    try:
                        if atom_sym_pairs[i+1][1] == bond_type[j^1]:
                            # found the bond
                            return pair[0]-atom_sym_pairs[i+1][0]
                    except IndexError:
                        # insert boundary condition check here
                        print(f"Bond occurence {bond_type[0]}-{bond_type[1]} not found")

    def preserve_structure(self, pos, bond_type, atom_sym_pairs):
        # find previous occurence of the bond to preserve structure
        print(f"Looking for {bond_type[0]}-{bond_type[1]}")
        previous_bond_pos = None
        for i in np.arange(pos, 0, -1):
            if (previous_bond_pos is None) and \
                    (atom_sym_pairs[i][1] == bond_type[0]):
                previous_bond_pos = atom_sym_pairs[i][0]
            try:
                if atom_sym_pairs[i][1] == bond_type[1] and \
                    atom_sym_pairs[i-1][1] == bond_type[0]:
                        # found last bond pair
                        if abs(previous_bond_pos[1]-atom_sym_pairs[i][0][1]) >\
                            abs(previous_bond_pos[1]-atom_sym_pairs[i-1][0][1]):
                            return atom_sym_pairs[i][0]
                        else:
                            return atom_sym_pairs[i-1][0]
            except IndexError:
                print("Bond - preserving  occurence not found")

    def translate_vectors(self, poscar, shift):
        x = float(input("Translate x: "))
        y = float(input("Translate y: "))
        z = float(input("Translate z: "))
        lattice = poscar['restruct_lattice']
        lattice[shift[0]:shift[1]] = map(lambda v:
                                         ([v[0][0]+x,
                                           v[0][1]+y,
                                           v[0][2]+z], v[1]),
                                         lattice[shift[0]:shift[1]])
        self.print_lattice(lattice, index_highlight=shift)
        poscar['restruct_lattice'] = lattice
        return poscar


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Atom resturcturer')
    parser.add_argument('source', type=str, help='source POSCAR file')
    parser.add_argument('out', type=str, help='output POSCAR file')
    parser.add_argument('--infer', help='infer x, y coords',
                        action='store_true')
    parser.add_argument('-s', '--shift', help='shift vector in range [start, stop)',
                        nargs=2, type=int)
    parser.add_argument('--flat', help='flat display with coordinates',
                        action='store_true')
    args = parser.parse_args()
    print(args)
    ar = AtomRestruct()
    if args.flat:
        ar.print_lattice = ar.print_lattice_flat
    poscar = ar.read_poscar(args.source)
    new_poscar = ar.lattice_positions(poscar, args.infer)
    if args.shift is not None:
        new_poscar = ar.translate_vectors(new_poscar, args.shift)
    print(f"Saving POSCAR file in {args.out}")
    ar.save_poscar(args.out, new_poscar)

