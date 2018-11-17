import argparse
import json
from multiprocessing import Pool


class Interface:
    def __init__(self, specification):
        self.arg_list = specification['specification']
        self.parsed_args = self.define_input_parameters(specification["description"])
        self.defined_parameters = [x['name'] for x in self.arg_list]

    def define_input_parameters(self, desc):
        parser = argparse.ArgumentParser(description=desc)
        for argument in self.arg_list:
            if 'short' in argument.keys():
                if 'action' in argument.keys():
                    parser.add_argument("-"+argument['short'], "--" + argument['name'],
                                        help=argument['help'],
                                        action=argument['action'])
                else:
                    parser.add_argument("-"+argument['short'], "--" + argument['name'],
                        help=argument['help'],
                        type=self.decode_type(argument['type']))     
            else:
                if 'action' in argument.keys():
                    parser.add_argument("--" + argument['name'],
                        help=argument['help'],
                        action=argument['action'])
                else:
                    parser.add_argument("--" + argument['name'],
                        help=argument['help'],
                        type=self.decode_type(argument['type']))
        return parser.parse_args()

    def decode_type(self, type_str):
        if type_str == "str":
            return str
        elif type_str == "int":
            return int
        elif type_str == "float":
            return float
        elif type_str == "bool":
            return bool


class ParsingStage:
    def __init__(self, interface):
        self.available_argument_list = interface.defined_parameters
        self.default_dict_path = "default_param_set.json"

        # immediately read the arguments
        self.resultant_dict = {}
        self.args = interface.parsed_args
        self.args_handler()

        self.read_json_dict_param(self.default_dict_path)

    def args_handler(self):
        for arg_name in self.available_argument_list:
            try:
                if getattr(self.args, arg_name) is not None:
                    self.set_dict_param(arg_name, getattr(self.args, arg_name))
            except TypeError:
                print("ASKED FOR NON-EXISTENT VALUE {}".format(arg_name))

    def set_dict_param(self, param_name, param_val):
        self.resultant_dict[param_name] = param_val

    def read_json_dict_param(self, filepath):
        with open(filepath, 'r') as f:
            default_dict = json.loads(f.read())
            print("CORRECT DICT TYPE? {}".format(str(type(default_dict))))
        print("DEFAULT DICTIONARY PARAMS DETECTED...\n{}".format(default_dict))

        if (not isinstance(default_dict, dict)) or \
                (not isinstance(self.resultant_dict, dict)):
            msg = "Dictionary mismatch of types"
            raise TypeError(msg)
        elif type(default_dict) != dict:
            raise TypeError("Invalid type of entry")

        # if self.resultant_dict["view"]:
        #     quit()
        # overwrite default dict with dict taken from arg parse
        # this line does it, mind the order!
        self.resultant_dict = {**default_dict, **self.resultant_dict}


def asynchronous_pool_order(func, args, object_list):
    pool = Pool()
    output_list = []
    multiple_results = [pool.apply_async(func, (*args, object_type))
                        for object_type in object_list]
    for result in multiple_results:
        value = result.get()
        output_list.append(value)
    return output_list