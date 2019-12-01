import argparse
import os


class KpointsPath:
    def __init__(self):
        self.k_symm = {
            'G': (0.0, 0.0, 0.0),
            'H': (0.5, -0.5, 0.5),
            'P': (0.25, 0.25, 0.25),
            'N': (0.0, 0.0, 0.5),
            'R': (0.5, 0.5, 0.5),
            'X': (0.0, 0.5, 0.0)
        }
        self.default_points = 40

    def create_kpoints_file(self, loc, path_strings):
        with open(os.path.join(loc, "KPOINTS"), 'w') as f:
            f.write("CREATED BY PYTHON VASP\n")
            f.write(f"{self.default_points}\n")
            f.write('Line-mode\n')
            f.write('rec\n')
            f.write(self.construct_path(path_strings))

    def construct_path(self, path_strings):
        text_string = ""
        for path_string in path_strings:
            path_string = path_string.upper()
            for i in range(len(path_string)-1):
                node = path_string[i]
                next_node = path_string[i+1]
                text_string += "{} {} {} ! {}\n".format(
                    *self.k_symm[node], node)
                text_string += "{} {} {} ! {}\n\n".format(
                    *self.k_symm[next_node], next_node)
        return text_string


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='KPATH constructor')
    parser.add_argument('-p', '--path', type=str, nargs='*',
                        help='path to be constructed')
    parser.add_argument('-s', '--save', type=str,
                        help='save KPOINTS file')
    parser.add_argument('--sample', type=int,
                        help='sample points')
    args = parser.parse_args()
    print(args)
    kp = KpointsPath()
    if args.sample is not None:
        kp.default_points = args.sample
    kp.create_kpoints_file(args.save, args.path)
