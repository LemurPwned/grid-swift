import re
import sys
import os
import argparse
import numpy as np
from functools import reduce
from collections import Counter

def rot_matrix_z(theta): return np.array([
    [np.cos(theta), -np.sin(theta), 0],
    [np.sin(theta), np.cos(theta), 0],
    [0, 0, 1]
])

def rot_matrix_y(theta): return np.array([
    [np.cos(theta), 0, np.sin(theta)],
    [0, 1, 0],
    [-np.sin(theta), 0, np.cos(theta)]
])

def rot_matrix_x(theta): return np.array([
    [1, 0, 0],
    [0, np.cos(theta), -np.sin(theta)],
    [0, np.sin(theta), np.cos(theta)]
])

class AtomRestruct:
    def __init__(self):
        self.regex = '\W+'
        self.lattice_subregex = '(-?[0-9]+\.?[0-9]+e?-?[0-9]*)'
        self.print_lattice = self.print_lattice_space
        self.lattice_constants = {
            "Pt": (3.92, 3.92, 3.92, 'fcc'),
            "Co": (3.5447, 3.5447, 3.5447, 'fcc'),
            "Co2": (2.50, 2.50, 4.695, 'hcp')
        }

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
            old_scaler = poscar['scaler']
            poscar['scaler'] = 1 \
                if poscar['coord_type'] == 'Direct' else poscar['scaler']
            f.write(f"      {str(poscar['scaler'])}\n")
            for row in poscar['basis']:
                to_write = np.array(row)*old_scaler \
                            if poscar['coord_type'] == 'Direct' else row
                print('    ', file=f, end='')
                print(*to_write, sep='  ', file=f, end='')
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

    def parse_coords(self, coords, coords_type, lattice_matrix,
                     lattice_scaler):
        match = re.findall(self.lattice_subregex, coords)
        try:
            fin_coord = np.array([float(i)
                                  for i in match])
            if (fin_coord is None) or (len(fin_coord) == 0):
                raise ValueError
        except ValueError:
            raise ValueError(f"Invalid lattice vector {coords}")
        try:
            if coords_type == 'Direct':
               return np.dot(lattice_matrix, fin_coord*lattice_scaler)
            else:
                return fin_coord
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
        poscar['basis'][2][2] = poscar['basis'][2][2] + zshift/poscar['scaler']
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
        spacing = {unique_plane[i]: '  '*i
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


    def transform_coordinates(self, coord_set, theta, phi):
        return [rot_matrix_x(phi)@rot_matrix_z(theta)@np.array(coord) 
                for coord in coord_set]

    def structure_generator(self, spec, out,
                            cube_type='fcc', miller='111',
                            theta=np.pi/4,
                            phi=np.arctan(np.sqrt(2)),
                            shift=0):
        """
        Assume that the structure given in the path_string is:
        A1 n1 A2 n2 A3 n3 ...
        where Ax is an atom, nx is the number of atoms
        """
        cube = [
            (0., 0., 0.), # 0
            (0., 0., 1.), # 1
            (0., 1., 0.), # 2 
            (0., 1., 1.), # 3
            (1., 0., 0.), # 4
            (1., 0., 1.), # 5
            (1., 1., 0.), # 6
            (1., 1., 1.), # 7
            (0, 0.5, 0.5),# 8
            (1, 0.5, 0.5),# 9
            (0.5, 0, 0.5),# 10
            (0.5, 1, 0.5),# 11
            (0.5, 0.5, 0),# 12
            (0.5, 0.5, 1),# 13
        ]
        """
        # inteplane distance => 1/d^2 = (h+k+l)/a^2
        # d = a*sqrt(3)/3
        transform the coordinate system to obtain the plane centering around z axis
        """
        new_coords = self.transform_coordinates(cube, theta, phi)
        """
        # fcc_111_planes = [[0],[1,4,2,8,10,12],[5,3,6,9,11,13], [7]]
        [7] is not included as a plane because it's equivalent to the [0] plane 
        in the neighbouring cell
        """
        fcc_111_planes = [[0],[1,4,2,8,10,12],[5,3,6,9,11,13]] 
        path_len = len(fcc_111_planes)
        atoms = spec[::2]
        planes = list(map(lambda x: int(x), spec[1::2]))
        atom_listing = {atom: [] for atom in atoms}
        result = []
        # meta lattice is the max lattice of all
        meta_lattice = np.max([self.lattice_constants[atom][0] for atom in atoms])*2
        print(f"Meta lattice is {meta_lattice} Å")
        if cube_type == 'fcc':
            zshift = 0.0 if shift is None else shift
            i = 0
            atm_cnt = 0
            for atom, monolayers in zip(atoms, planes):
                current_atom_num = 0
                for monolayer in range(monolayers):
                    current_plane = fcc_111_planes[i%path_len]
                    current_atom_num += len(current_plane) # number of atoms in the current_plane
                    try:
                        current_lattice_constants = np.array(self.lattice_constants[atom][:3])
                        # this should be the cuboid spacing
                        plane_spacing = current_lattice_constants[2]*np.sqrt(3)/3 
                        # modify plane spacing if we are at the interface (don't take 0, always resolve for monolayers-1)
                        if monolayer == monolayers-1:
                            foreign_spacing = self.lattice_constants[atoms[atm_cnt-1]][2]*np.sqrt(3)/3
                            # take the mean
                            plane_spacing = (plane_spacing + foreign_spacing)/2
                            print(f"Calculated interface spacing: {atoms[atm_cnt-1]}/{atoms[atm_cnt]} Å",
                                f"as mean: {np.around(foreign_spacing, decimals=3)} Å,{np.around(plane_spacing, decimals=3)} Å")
                    except KeyError:
                        raise ValueError(f"Lattice constants for {atom} not found!")
                    for position in current_plane:
                        current_position_base = new_coords[position]
                        atom_listing[atom].append(
                            (
                            *(current_position_base[:2]*current_lattice_constants[:2]
                            -np.array([meta_lattice, meta_lattice])/2
                            ).tolist() ,
                            zshift
                        )
                        )
                        result.append(
                            (
                            *(current_position_base[:2]*current_lattice_constants[:2]
                            -np.array([meta_lattice, meta_lattice])/2
                            ).tolist() ,
                            zshift
                        )
                        )
                    i += 1
                    zshift += plane_spacing # separate each monolayer
                atm_cnt += 1
        else:
            raise ValueError(f"Argument cube type of {cube_type} is not supported.")

        filepath = os.path.join(out, 'POSCAR')
        # reduce the atoms and their number
        key_order = atom_listing.keys()
        atm_str = ' '.join(key_order) 
        num_str = ' '.join([str(len(atom_listing[key])) for key in key_order]) 
        with open(filepath, 'w') as f:
            f.write(f"{''.join(spec)}" + '\n')
            f.write(f"     1.0\n")
            f.write(f"       {meta_lattice} 0.0 0.0\n")
            f.write(f"       0.0 {meta_lattice} 0.0\n")
            f.write(f"       0.0 0.0 {zshift}\n")
            f.write(f"      {atm_str}\n")
            f.write(f"      {num_str}\n")
            f.write('Cart\n')
            for key in atom_listing: # this ensures atoms are in order
                for pos in atom_listing[key]:
                    f.write("  {} {} {}\n".format(*pos))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Atom resturcturer')
    parser.add_argument('--source', type=str, help='source POSCAR file')
    parser.add_argument('--out', type=str, help='output POSCAR file')
    parser.add_argument('--infer', help='infer x, y coords',
                        action='store_true')
    parser.add_argument('-s', '--shift', help='shift vector in range [start, stop)',
                        nargs=2, type=int)
    parser.add_argument('--offset', help='offset in z dim for structure builder', type=float)
    parser.add_argument('--flat', help='flat display with coordinates',
                        action='store_true')
    parser.add_argument('--path', help='path', nargs='*')
    args = parser.parse_args()
    print(args)
    ar = AtomRestruct()
    if args.path:
        if args.out is None:
            raise ValueError("Invalid output path for POSCAR specified")
        ar.structure_generator(spec=args.path, out=args.out, shift=args.offset)
        quit()
    if args.flat:
        ar.print_lattice = ar.print_lattice_flat
    poscar = ar.read_poscar(args.source)
    new_poscar = ar.lattice_positions(poscar, args.infer)
    if args.shift is not None:
        new_poscar = ar.translate_vectors(new_poscar, args.shift)
    print(f"Saving POSCAR file in {args.out}")
    ar.save_poscar(args.out, new_poscar)

