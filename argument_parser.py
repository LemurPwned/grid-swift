class Parser:
    def __init__(self):
        parser = argparse.ArgumentParser(description='V.A.S.P Simualtion Manager')
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