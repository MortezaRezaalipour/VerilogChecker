import os
import re
import subprocess
from typing import Dict, List
from tempfile import mkstemp
from shutil import move, copymode

from checker import extract_inputs_outputs, extract_module_signature



def fix_module_name(input_path: str):
    file = input_path.split('/')[-1]
    subst = file[:file.rfind('.')]  # get pure name
    fh, abs_path = mkstemp()
    with os.fdopen(fh, 'w') as new_file:
        with open(input_path) as old_file:
            for line in old_file:
                if 'module' in line and 'endmodule' not in line:

                    # This pattern divides the module declaration into three parts.
                    # for example: it divides this: module \nulls9-ko23iou09vn2adder(pi0, pi1, pi2, pi3, po0, po1, po2);\n
                    # into this:
                    # match.group(1) <= 'module '
                    # match.group(2) <= '\nulls9-ko23iou09vn2adder'
                    # match.group(1) <= '(pi0, pi1, pi2, pi3, po0, po1, po2);\n'
                    pattern = '(module )([^\(]+)(\(.*\);)'
                    match = re.search(pattern, line)
                    second = match.group(2)
                    new_file.write(line.replace(second, subst))
                else:
                    new_file.write(line)
    copymode(input_path, abs_path)
    os.remove(input_path)
    move(abs_path, input_path)



def synthesize_to_gate_level(input_path: str, output_path: str):

    fix_module_name(input_path)


    yosys_command = f"""
    read_verilog {input_path};
    synth -flatten;
    opt;
    opt_clean -purge;
    abc -g NAND;
    opt;
    opt_clean -purge;
    splitnets -ports;
    opt;
    opt_clean -purge;
    write_verilog -noattr {output_path};
    """
    process = subprocess.run(['yosys', '-p', yosys_command], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if process.stderr.decode():
        print(f'Error!')
        raise Exception(f'ERROR!!! yosys cannot do its pass on file {input_path}\n{process.stderr.decode()}')

    return rename_variables(output_path, output_path)



def rename_variables(input_path: str, output_path: str):
    with open(f'{input_path}', 'r') as infile:
        verilog_str = infile.read()

    verilog_str_tmp = verilog_str.split(';')
    verilog_str = verilog_str.split('\n')

    module_name, port_list = extract_module_signature(verilog_str_tmp)
    input_dict, output_dict = extract_inputs_outputs(verilog_str_tmp, port_list)

    new_labels = create_new_labels(port_list, input_dict, output_dict)
    verilog_str = relabel_nodes(verilog_str, new_labels)

    with open(f'{output_path}', 'w') as outfile:
        for line in verilog_str:
            outfile.write(f'{line}\n')

    new_input_dict = {}
    new_output_dict = {}
    for inkey in input_dict.keys():
        invalue = input_dict[inkey]
        if invalue[0] in new_labels.keys():
            new_input_dict[inkey] = (new_labels[invalue[0]], invalue[1])

    for outkey in output_dict.keys():
        outvalue = output_dict[outkey]
        if outvalue[0] in new_labels.keys():
            new_output_dict[outkey] = (new_labels[outvalue[0]], outvalue[1])


    # I'm just returning these because I need them later
    return module_name, port_list, new_input_dict, output_dict

def create_new_labels(port_list: List, input_dict: Dict, output_dict: Dict):
    new_labels: Dict = {}
    for port_idx in input_dict:
        if input_dict[port_idx][0] == port_list[port_idx]:
            new_labels[port_list[port_idx]] = f'in{port_idx}'
        else:
            raise Exception(f'Error!!! {input_dict[port_idx][0]} is not equal to {port_list[port_idx]}')

    out_idx = 0
    for port_idx in output_dict:
        if output_dict[port_idx][0] == port_list[port_idx]:
            new_labels[port_list[port_idx]] = f'out{out_idx}'
            out_idx += 1
        else:
            raise Exception(f'Error!!! {output_dict[port_idx][0]} is not equal to {port_list[port_idx]}')
    return new_labels


def relabel_nodes(verilog_str: List[str], new_labels: Dict):
    verilog_str_tmp = verilog_str

    for line_idx, line in enumerate(verilog_str):
        for key, value in new_labels.items():

            escaped_key = re.escape(key)
            if re.search(f'{escaped_key}[,;)\s\n\r]|({escaped_key})$', line):
                found = re.search(f'({escaped_key})[,;)\s\r\n]|({escaped_key})$', line)
                middle = found.group(1)
                end = found.group(2)

                s = found.span()[0]
                if found.group(1):
                    e = s + len(found.group(1))
                    line = f"{line[:s]}{value}{line[e:]}"
                elif found.group(2):
                    line = f"{line[:s]}{value}"
                else:
                    print(
                        Fore.RED + f'ERROR! in (__name__): variable{key} does not belong in either of the two groups!' + Style.RESET_ALL)
                # print(f'{line  =}')
                verilog_str_tmp[line_idx] = line
            # if key in line:
            #     print(f'{key = }')
            #     print(f'{line = }')
            #     exit()
    return verilog_str_tmp
    # verilog_str_tmp = verilog_str
    # for line_idx, line in enumerate(verilog_str):
    #     for key, value in new_labels.items():
    #         if key in line:
    #             line = line.replace(key, value)
    #             verilog_str_tmp[line_idx] = line
    # return verilog_str_tmp

