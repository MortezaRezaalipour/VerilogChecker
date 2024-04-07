import os
import sys
import subprocess
import re
import random
import argparse
from typing import List, Dict, Callable, Literal
from collections import OrderedDict
from yosys_pass import *

INPUT_ORDER_TYPE1 = '1'  # [n:0]a, [n:0]b => circuit(a0, a1, ..., an, b0, b1, ..., bn, [outputs])
INPUT_ORDER_TYPE2 = '2'  # [n:0]a, [n:0]b => circuit(an, an-1, ..., a0, bn, bn-1, ..., b0, [outputs])

OUTPUT_ORDER_TYPE1 = '1'  # [n:0]y, [n:0]z => circuit([inputs], y0, y1, ..., yn, z0, z1, ..., zn)
OUTPUT_ORDER_TYPE2 = '2'  # [n:0]y, [n:0]z => circuit([inputs], yn, yn-1, ..., y0, zn, zn-1, ..., z0)

class CustomAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # Your custom action here. For example, set a specific value or modify the values argument.
        # Then set the attribute in the namespace
        setattr(namespace, self.dest, list(values))

class Arguments:
    def __init__(self, tmp_args):
        self.__circuits = tmp_args.input
        self.__input_port_orders = tmp_args.input_port_orders
        self.__output_port_orders = tmp_args.output_port_orders
        self.__et = tmp_args.error_threshold
        if tmp_args.metric_type == 'wae':
            self.__metric_type = wae
        elif tmp_args.metric_type == 'med':
            self.__metric_type = med
        elif tmp_args.metric_type == 'msed':
            self.__metric_type = msed
        elif tmp_args.metric_type == 'er':
            self.__metric_type = er
        elif tmp_args.metric_type == 'mred':
            self.__metric_type = mred

        self.__check = bool(tmp_args.check)
        self.__evaluate = bool(tmp_args.evaluate)



    @property
    def check(self):
        return self.__check

    @property
    def evaluate(self):
        return self.__evaluate

    @property
    def metric_type(self):
        return self.__metric_type

    @property
    def et(self):
        return self.__et

    @property
    def circuits(self):
        return self.__circuits

    @property
    def input_port_orders(self):
        return self.__input_port_orders

    @property
    def output_port_orders(self):
        return self.__output_port_orders

    @classmethod
    def parse(cls):
        my_parser = argparse.ArgumentParser(description='equivalence checker',
                                            prog='verifier.py',
                                            usage='%(prog)s ...')

        my_parser.add_argument('--input', '-i', help='path-to-circuit(s)', action='append')
        my_parser.add_argument('--input_port_orders', '-ipo', help='port-order(s)', action=CustomAction, choices=['11', '12', '21', '22'], type=str,
                               default=['1', '1'])
        my_parser.add_argument('--output_port_orders', '-opo', help='port-order(s)', action=CustomAction, choices=['11', '12', '21', '22'] , type=str,
                               default=['1', '1'])
        my_parser.add_argument('--error_threshold', '-et', help='error-threshold', type=float, default=-1)
        metrics = ['wae', 'med', 'msed', 'er', 'mred']
        my_parser.add_argument('--metric_type', '-t', help='metric-type', type=str, choices=metrics, default='wae')
        my_parser.add_argument('--check', action="store_true", help='check-weather-it-adheres-to-et')
        my_parser.add_argument('--evaluate', action="store_true", help='evaluate-the-metric-passed')
        tmp_args = my_parser.parse_args()


        return Arguments(tmp_args)

    def __repr__(self):
        return f'An object of class Arguments:\n' \
               f'{self.circuits = }\n' \
               f'{self.input_port_orders = }\n' \
               f'{self.output_port_orders = }\n' \
               f'{self.metric_type = }\n' \
               f'{self.check = }\n' \
               f'{self.evaluate = }\n' \
               f'{self.et = }\n'



class Circuit:
    def __init__(self):
        self.name = None
        self.ver_str = None
        self.synth_ver_str = None
        self.path = None
        self.synth_path = None
        self.input_dict = None
        self.input_count = None
        self.output_dict = None
        self.output_count = None
        self.input_order = None
        self.output_order = None
        self.testbench_path = None
        self.results_path = None
        self.simulation_pattern = None
        self.simulation_output = None




def main():
    args = Arguments.parse()
    print(f'{args = }')

    circuit1 = Circuit()
    circuit2 = Circuit()
    circuit1.path = args.circuits[0]
    circuit2.path = args.circuits[1]
    circuit1.input_order = args.input_port_orders[0]
    circuit2.input_order = args.input_port_orders[1]
    circuit1.output_order = args.output_port_orders[0]
    circuit2.output_order = args.output_port_orders[1]



    os.makedirs('report', exist_ok=True)
    os.makedirs('temp', exist_ok=True)

    circuit1.synth_path = f'temp/circuit1_syn.v'
    circuit2.synth_path = f'temp/circuit2_syn.v'

    name1, portlist1, input_dict1, output_dict1 = synthesize_to_gate_level(circuit1.path, circuit1.synth_path)
    name2, portlist2, input_dict2, output_dict2 = synthesize_to_gate_level(circuit2.path, circuit2.synth_path)
    circuit1.name = name1
    circuit2.name = name2



    circuit1.testbench_path = f'temp/{circuit1.name}_tb.v'
    circuit2.testbench_path = f'temp/{circuit2.name}_tb.v'
    circuit1.input_dict = input_dict1
    circuit2.input_dict = input_dict2
    circuit1.input_count = get_num_inputs(circuit1.input_dict)
    circuit2.input_count = get_num_inputs(circuit2.input_dict)
    circuit1.output_dict = output_dict1
    circuit2.output_dict = output_dict2
    circuit1.output_count = get_num_outputs(circuit1.output_dict)
    circuit2.output_count = get_num_outputs(circuit2.output_dict)

    assert circuit1.input_count == circuit2.input_count, "input counts are not equal!!!"
    assert circuit1.output_count == circuit2.output_count, "output counts are not equal!!!"

    with open(circuit1.path, 'r') as f1:
        circuit1.ver_str = f1.readlines()
    with open(circuit1.synth_path, 'r') as f1:
        circuit1.synth_ver_str = f1.readlines()
    with open(circuit2.path, 'r') as f2:
        circuit2.ver_str = f2.readlines()
    with open(circuit2.synth_path, 'r') as f2:
        circuit2.synth_ver_str = f2.readlines()

    samples = generate_samples(circuit1.input_count)
    circuit1.simulation_pattern = samples
    circuit2.simulation_pattern = samples

    assert circuit1.simulation_pattern == circuit2.simulation_pattern, "simulation patterns are not the same"

    simulate(circuit1)
    import_results(circuit1)
    simulate(circuit2)
    import_results(circuit2)

    # Now the circuit objects are filled and ready for equivalence check or evaluation
    if args.check:
        if check(circuit1, circuit2, args):
            print(f'Check -> PASSED!')
        else:
            print(f'Error Breached!!!')
    elif args.evaluate:
        error = evaluate(circuit1, circuit2, args)
        print(f'{error = }')
    else:
        AssertionError('Both check and evaluate flags are False! at least one should be True!')




def export_testbench(output_path: str, testbench: str):
    with open(output_path, 'w') as t:
        t.writelines(testbench)


def import_results(circuit: Circuit):
    # temp_results: List[int] = []
    with open(circuit.results_path, 'r') as r1:
        temp_results = r1.readlines()
    # for line_idx in range(len(temp_results_file)):
    #     temp_results.append(int(temp_results_file[line_idx].strip().strip("\n"), base=2))
    circuit.simulation_output = temp_results



def simulate(circuit: Circuit):
    # create testbench
    testbench = create_testbench(circuit, circuit.simulation_pattern)
    # export testbench
    export_testbench(circuit.testbench_path, testbench)
    # run testbenches
    result_path = f'temp/{circuit.name}.txt'
    circuit.results_path = result_path
    run_testbench(circuit.testbench_path, circuit.synth_path, circuit.results_path)



def check(circuit1: Circuit, circuit2: Circuit, args: Arguments) -> bool:
    error = args.metric_type(circuit1.simulation_output, circuit2.simulation_output)
    if error > args.et:
        return  False
    else:
        return True



def evaluate(circuit1: Circuit, circuit2: Circuit, args: Arguments) -> float:
    error = args.metric_type(circuit1.simulation_output, circuit2.simulation_output)
    return error


def wae(result1: List[str], result2: List[str]) -> int:
    """
    takes in two sets of correspondant outputs and compare the Worst-Absolute Error (WAE) of them.
    :param result1_path: the output bit-stream of the first circuit
    :param result2_path: the output bit-stream of the second circuit
    :return: the worst absolute error as an integer
    """

    assert len(result1) == len(result2) and len(
        result1) != 0, f"the number of outputs is not equal or they are zero in length"
    wae = 0
    for line_idx in range(len(result1)):
        # print(result1[line_idx].strip().strip("\n"))

        cur1 = abs(int(result1[line_idx].strip().strip("\n"), base=2))
        cur2 = abs(int(result2[line_idx].strip().strip("\n"), base=2))

        if wae < abs(cur1 - cur2):
            wae = abs(cur1 - cur2)

    return wae

def med(result1: List[str], result2: List[str]) -> float:
    """
    takes in two sets of correspondant outputs and compare the Mean-Error Distance (MED) of them.
    :param result1_path: the output bit-stream of the first circuit
    :param result2_path: the output bit-stream of the second circuit
    :return: the worst absolute error as an integer
    """

    assert len(result1) == len(result2) and len(
        result1) != 0, f"the number of outputs is not equal or they are zero in length"
    error_sum = 0
    for line_idx in range(len(result1)):


        cur1 = abs(int(result1[line_idx].strip().strip("\n"), base=2))
        cur2 = abs(int(result2[line_idx].strip().strip("\n"), base=2))

        error_sum += abs(cur1 - cur2)


    return float(error_sum / len(result1))

def er(result1: List[str], result2: List[str]) -> float:
    """
    takes in two sets of correspondant outputs and compare the Error Rate (ER) of them.
    :param result1_path: the output bit-stream of the first circuit
    :param result2_path: the output bit-stream of the second circuit
    :return: the worst absolute error as an integer
    """
    assert len(result1) == len(result2) and len(
        result1) != 0, f"the number of outputs is not equal or they are zero in length"
    unequal_count = 0
    for line_idx in range(len(result1)):
        # print(result1[line_idx].strip().strip("\n"))

        cur1 = abs(int(result1[line_idx].strip().strip("\n"), base=2))
        cur2 = abs(int(result2[line_idx].strip().strip("\n"), base=2))

        if cur1 != cur2:
            unequal_count += 1


    return float((unequal_count / len(result1)) * 100) # to get the percentage

def mred(result1: List[str], result2: List[str]) -> float:
    """
    takes in two sets of correspondant outputs and compare the Mean-Relative Error Distance (MRED) of them.
    :param result1_path: the output bit-stream of the first circuit
    :param result2_path: the output bit-stream of the second circuit
    :return: the worst absolute error as an integer
    """
    assert len(result1) == len(result2) and len(
        result1) != 0, f"the number of outputs is not equal or they are zero in length"
    sum_relative_error = 0
    uncounted = 0
    for line_idx in range(len(result1)):
        cur1 = abs(int(result1[line_idx].strip().strip("\n"), base=2))
        cur2 = abs(int(result2[line_idx].strip().strip("\n"), base=2))


        if cur1 != 0 and cur2 != 0:
            sum_relative_error += abs(cur1 - cur2) / cur1
        else:
            uncounted += 1

        print(f'{sum_relative_error= }')
        print(f'{len(result1) = }')
        print(f'{uncounted= }')
    return float((sum_relative_error / (len(result1) - uncounted)) * 100)  # to get the percentage


def msed(result1: List[str], result2: List[str]) -> float:
    """
    takes in two sets of correspondant outputs and compare the Mean-Squared Error Distance (MSED) of them.
    :param result1_path: the output bit-stream of the first circuit
    :param result2_path: the output bit-stream of the second circuit
    :return: the worst absolute error as an integer
    """
    assert len(result1) == len(result2) and len(
        result1) != 0, f"the number of outputs is not equal or they are zero in length"
    error_sum_squared = 0
    for line_idx in range(len(result1)):
        # print(result1[line_idx].strip().strip("\n"))

        cur1 = abs(int(result1[line_idx].strip().strip("\n"), base=2))
        cur2 = abs(int(result2[line_idx].strip().strip("\n"), base=2))

        error_sum_squared += abs(cur1 - cur2) * abs(cur1 - cur2)
    return float(error_sum_squared / len(result1))



def run_testbench(testbench_path: str, dut_path: str, result_path: str):
    iverilog_command = f'iverilog -o temp/temp.iv ' \
                       f'{dut_path} ' \
                       f'{testbench_path} '

    vvp_command = f'temp/temp.iv'

    with open(f'temp/iverilog_log.txt', 'w') as f:
        subprocess.call(iverilog_command, shell=True, stdout=f)

    with open(f'{result_path}', 'w') as f:
        subprocess.call(['vvp', vvp_command], stdout=f)


def extract_module_signature(verilog_str: List[str]):
    """
    reads the first line of a Verilog netlist and extracts module and port names
    :param verilog_str1: the Verilog description as a string
    :return: modulename as a string variable and port names as a list
    """
    module_name = None
    port_list = None

    for line in verilog_str:
        line = line.strip()  # remove whitespaces at the beginning or end of the line

        if re.search('module', line) and not re.search('endmodule', line):
            # extract module

            match_object = re.search('module (\w+)', line)  # module adder(a, b, c)
            module_name = match_object.group(1)  # adder

            # extract port list

            line = line.split(module_name)[1].replace("\n", "").strip()

            match_object = re.search('\((.+)\)', line)  # module adder(a, b, c)

            ports_str = match_object.group(1)  # a, b, c

            port_list = ports_str.strip().replace(" ", "").split(',')
    assert module_name and port_list, f'Either module_name or port_list is None'
    return module_name, port_list


def extract_inputs_outputs(verilog_str: List[str], port_list: List[str]):
    input_dict: Dict[int:(str, int)] = {}
    output_dict: Dict[int:(str, int)] = {}
    # example:
    # for module circuit(a, b, c, d)
    # input [1:0] a;
    # input [2:0]b;
    # output d;
    # output [3:0]c;
    # example input_dict = {0:(a, 2), 1:(b, 3)}
    # example input_dict = {3:(d, 1), 2:(c, 3)}

    for line in verilog_str:
        line = line.strip()  # remove all whitespaces at the beginning or end of the line
        # extract inputs
        if line.startswith('input'):
            match_obj = re.search('input (.+)', line)  # input a, b, c; or input [1:0] a;
            cur_input_str = match_obj.group(1)  # a, b, c or [1:0] a
            cur_input_list = cur_input_str.strip().replace(" ", "").split(',')  # ['a', 'b', 'c'] or ['[1:0]a']
            cur_input_list = check_multi_vector_declaration(cur_input_list)
            for inp in cur_input_list:

                if get_name(inp) in port_list:
                    position_in_module_signature = port_list.index(get_name(inp))
                    input_dict[position_in_module_signature] = (get_name(inp), get_width(inp))
                else:

                    raise Exception(f"input name {get_name(inp)} is not in the port_list {port_list}")
        # extract outputs
        if line.startswith('output'):
            match_obj = re.search('output (.+)', line)  # input a, b, c; or input [1:0] a;
            cur_output_str = match_obj.group(1)  # a, b, c or [1:0] a
            cur_output_list = cur_output_str.strip().replace(" ", "").split(',')  # ['a', 'b', 'c'] or ['[1:0]a']
            cur_output_list = check_multi_vector_declaration(cur_output_list)
            for out in cur_output_list:
                if get_name(out) in port_list:
                    position_in_module_signature = port_list.index(get_name(out))
                    output_dict[position_in_module_signature] = (get_name(out), get_width(out))
                else:
                    raise Exception(f"output name {get_name(out)} is not in the port_list")
        sorted_input_dict = OrderedDict(sorted(input_dict.items()))
        sorted_output_dict = OrderedDict(sorted(output_dict.items()))
    return input_dict, output_dict


def check_multi_vector_declaration(cur_list: List[str]) -> List[str]:
    # for lines such as:
    # input [1:0]a, b;
    # cur_list will be = ['[1:0]a', 'b'] which should be ['[1:0]a', '[1:0]b']
    if is_vector(cur_list[0]):
        # find the range
        vector_range = re.search('\[\d+:\d+\]', cur_list[0]).group()
        # propagate the range for the rest of the elements of cur_list
        for i in range(1, len(cur_list)):
            cur_list[i] = vector_range + cur_list[i]
    return cur_list


def is_vector(var_name: str) -> bool:
    """
    checks whether var_name variable is a vector
    :param var_name: the variable name
    :return: True if the variable is a vector, otherwise returns False
    """
    if re.search('(\[\d+:\d+\])', var_name):
        return True
    else:
        return False


def get_width(var_name: str) -> int:
    """
    computes the bit-width of a given variable
    :param var_name: the name of the variable
    :return: an integer representing the bit-width of the given variable
    """
    if is_vector(var_name):
        # compute the length
        match = re.search('\[(\d+):(\d+)\]', var_name)  # [1:0]a
        l_bound = int(match.group(1))  # 1
        r_bound = int(match.group(2))  # 0
        return abs((l_bound - r_bound) + 1)
    else:
        return 1


def get_name(var_name: str) -> str:
    """
    if var_name is an array, e.g., [1:0]a, it will return a. Otherwise, it will return var_name.
    :param var_name: the name of the variable
    :return: a string representing variable name
    """
    if is_vector(var_name):
        # remove [n:m] part
        match_obj = re.search('(\[\d+:\d+\])(.*)', var_name)
        return match_obj.group(2)
    else:
        return var_name


def create_testbench(circuit_obj: Circuit, samples: List[int]) -> str:
    testbench = ''
    module_signature = f'module {circuit_obj.name}_tb;\n'

    # input/output declaration

    input_dec = f'reg [{circuit_obj.input_count - 1}:0]pi;\n'

    output_dec = f'wire [{circuit_obj.output_count - 1}:0]po;\n'

    # instantiate dut
    instatiate_dut = instantiate_dut(circuit_obj)

    # apply samples
    mapped_samples = f'initial\n' \
                     f'begin\n'
    for sample in samples:
        mapped_samples += integer_to_binary(circuit_obj, sample)
    mapped_samples += f'end\n' \
                      f'endmodule\n'

    testbench = module_signature + input_dec + output_dec + instatiate_dut + mapped_samples

    return testbench


def instantiate_dut(circuit_obj: Circuit):
    instatiate_dut = f'{circuit_obj.name} dut ('

    if circuit_obj.input_order == INPUT_ORDER_TYPE1:
        for input_idx in range(circuit_obj.input_count):
            instatiate_dut += f'pi[{input_idx}], '

    elif circuit_obj.input_order == INPUT_ORDER_TYPE2:
        for input_idx in range(circuit_obj.input_count-1, -1, -1):

            instatiate_dut += f'pi[{input_idx}], '
    else:
        raise Exception('Input order is unknown!')


    if circuit_obj.output_order == OUTPUT_ORDER_TYPE1:
        for output_idx in range(circuit_obj.output_count):
            if output_idx == circuit_obj.output_count - 1:
                instatiate_dut += f'po[{output_idx}]'
            else:
                instatiate_dut += f'po[{output_idx}], '

    elif circuit_obj.output_order == OUTPUT_ORDER_TYPE2:

        for output_idx in range(circuit_obj.output_count -1, -1, -1):
            if output_idx == 0:
                instatiate_dut += f'po[{output_idx}]'
            else:
                instatiate_dut += f'po[{output_idx}], '
    else:
        raise Exception('Output order is unknown!')

    instatiate_dut += f');\n'

    return instatiate_dut


def integer_to_binary(circuit_obj: Circuit, sample: int):
    mapped_sample = f''

    binary_sample = integer_sample_to_binary(circuit_obj, sample)

    mapped_sample += f"# 1 pi={circuit_obj.input_count}'b{binary_sample};\n" \
                     f"#1 $display(\"%b\", po);\n"

    return mapped_sample


def integer_sample_to_binary(circuit_obj: Circuit, sample: int):
    if circuit_obj.input_order == INPUT_ORDER_TYPE1:
        return f'{sample:0{circuit_obj.input_count}b}'
    elif circuit_obj.input_order == INPUT_ORDER_TYPE2:
        # Split sample in half and reorder it
        sample = reorder_string(f'{sample:0{circuit_obj.input_count}b}')
        return sample
    else:
        raise Exception('Input order is unknown!')

def reorder_string(s):
    # Split the string into 2-character chunks
    parts = []


    parts.append(s[0:len(s)//2])
    parts.append(s[len(s)//2:])

    parts[0] = parts[0][::-1]
    parts[1] = parts[1][::-1]

    return parts[0]+parts[1]




def get_num_inputs(input_dict: Dict) -> int:
    """
    returns the bitwidth of the input to the module
    :param input_dict: the dictionary containing the inputs alongside their bitwidth
    :return: an integer representing the module's input bitwidth
    """
    count = 0
    for idx in input_dict.keys():
        count += input_dict[idx][1]
    return count


def get_num_outputs(output_dict: Dict) -> int:
    """
    returns the bitwidth of the outputs of the module
    :param output_dict: the dictionary containing the outputs alongside their bitwidth
    :return: an integer representing the module's output bitwidth
    """
    count = 0
    for idx in output_dict.keys():
        count += output_dict[idx][1]
    return count


def generate_samples(input_count: int) -> List[int]:
    if input_count <= 10:
        print(f'Exhaustive Simulation')
        return list(range(2 ** input_count))
    else:
        print(f'Monte Carlo Simulation')
        return random.sample(range(0, 2 ** input_count), 1000)


if __name__ == "__main__":
    main()

