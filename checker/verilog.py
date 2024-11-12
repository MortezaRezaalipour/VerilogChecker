import re
from typing import List, Dict, Tuple
from collections import OrderedDict
import os
from shutil import move, copymode
from tempfile import mkstemp
import colorama
from colorama import Fore, Style
colorama.init(autoreset=True)
class VerilogProcessor:
    """
        This class provides methods for processing Verilog files, including fixing module names,
        renaming variables, and extracting input/output information.
        """
    # ====================== MODULE NAME FIXING ======================
    def _fix_module_name(self, input_path: str):
        """
        Modifies the module name in the Verilog file to match the filename without the extension.

        Args:
            input_path (str): The path to the Verilog file to be processed.

        Raises:
            Exception: If an error occurs during file processing.
        """
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
    # ====================== VARIABLE RENAMING ======================
    def _rename_variables(self, input_path: str, output_path: str):
        """
        Renames variables within a Verilog file based on a new label mapping.

        Args:
            input_path (str): Path to the original Verilog file.
            output_path (str): Path to save the modified Verilog file.

        Returns:
            Tuple[str, List[str], Dict, Dict]: The module name, port list,
            input dictionary, and output dictionary for the processed file.
        """
        with open(f'{input_path}', 'r') as infile:
            verilog_str = infile.read()

        verilog_str_tmp = verilog_str.split(';')
        verilog_str = verilog_str.split('\n')

        module_name, port_list = self._extract_module_signature(verilog_str_tmp)
        input_dict, output_dict = self._extract_inputs_outputs(verilog_str_tmp, port_list)

        new_labels = self._create_new_labels(port_list, input_dict, output_dict)
        verilog_str = self._relabel_nodes(verilog_str, new_labels)

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

    def _create_new_labels(self, port_list: List, input_dict: Dict, output_dict: Dict):
        """
        Creates new labels for variables based on port list and input/output dictionaries.

        Args:
            port_list (List): List of port names.
            input_dict (Dict): Dictionary of input ports.
            output_dict (Dict): Dictionary of output ports.

        Returns:
            Dict: A dictionary mapping old variable names to new labels.
        """
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

    def _relabel_nodes(self, verilog_str: List[str], new_labels: Dict):
        """
        Replaces old variable names with new labels in the Verilog code.

        Args:
            verilog_str (List[str]): Lines of Verilog code.
            new_labels (Dict): Dictionary mapping old names to new labels.

        Returns:
            List[str]: Modified Verilog code with relabeled nodes.
        """
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
                    verilog_str_tmp[line_idx] = line
        return verilog_str_tmp

    def _extract_module_signature(self, verilog_str: List[str]):
        """
        Extracts the module name and port list from the Verilog file.

        Args:
            verilog_str (List[str]): Lines of Verilog code.

        Returns:
            Tuple[str, List[str]]: The module name and list of port names.
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

    def _extract_inputs_outputs(self, verilog_str: List[str], port_list: List[str]):
        """
        Extracts inputs and outputs from the Verilog code.

        Args:
            verilog_str (List[str]): Lines of Verilog code.
            port_list (List[str]): List of ports in the module.

        Returns:
            Tuple[Dict[int, Tuple[str, int]], Dict[int, Tuple[str, int]]]: Dictionaries for input and output ports.
        """
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
                cur_input_list = self._check_multi_vector_declaration(cur_input_list)
                for inp in cur_input_list:

                    if self._get_name(inp) in port_list:
                        position_in_module_signature = port_list.index(self._get_name(inp))
                        input_dict[position_in_module_signature] = (self._get_name(inp), self._get_width(inp))
                    else:

                        raise Exception(f"input name {self._get_name(inp)} is not in the port_list {port_list}")
            # extract outputs
            if line.startswith('output'):
                match_obj = re.search('output (.+)', line)  # input a, b, c; or input [1:0] a;
                cur_output_str = match_obj.group(1)  # a, b, c or [1:0] a
                cur_output_list = cur_output_str.strip().replace(" ", "").split(',')  # ['a', 'b', 'c'] or ['[1:0]a']
                cur_output_list = self._check_multi_vector_declaration(cur_output_list)
                for out in cur_output_list:
                    if self._get_name(out) in port_list:
                        position_in_module_signature = port_list.index(self._get_name(out))
                        output_dict[position_in_module_signature] = (self._get_name(out), self._get_width(out))
                    else:
                        raise Exception(f"output name {self._get_name(out)} is not in the port_list")
            sorted_input_dict = OrderedDict(sorted(input_dict.items()))
            sorted_output_dict = OrderedDict(sorted(output_dict.items()))
        return input_dict, output_dict

    def _check_multi_vector_declaration(self, cur_list: List[str]) -> List[str]:
        """
        Expands vector declarations across multiple variables.

        Args:
            cur_list (List[str]): List of variables.

        Returns:
            List[str]: List of variables with consistent vector ranges.
        """
        # for lines such as:
        # input [1:0]a, b;
        # cur_list will be = ['[1:0]a', 'b'] which should be ['[1:0]a', '[1:0]b']
        if self._is_vector(cur_list[0]):
            # find the range
            vector_range = re.search('\[\d+:\d+\]', cur_list[0]).group()
            # propagate the range for the rest of the elements of cur_list
            for i in range(1, len(cur_list)):
                cur_list[i] = vector_range + cur_list[i]
        return cur_list

    def _is_vector(self, var_name: str) -> bool:
        """
        Checks if a variable is a vector.

        Args:
            var_name (str): The variable name.

        Returns:
            bool: True if the variable is a vector, False otherwise.
        """
        if re.search('(\[\d+:\d+\])', var_name):
            return True
        else:
            return False

    def _get_name(self, var_name: str) -> str:
        """
        Extracts the name of a variable, ignoring vector indices.

        Args:
            var_name (str): The variable name.

        Returns:
            str: The base name of the variable.
        """
        if self._is_vector(var_name):
            # remove [n:m] part
            match_obj = re.search('(\[\d+:\d+\])(.*)', var_name)
            return match_obj.group(2)
        else:
            return var_name

    def _get_width(self, var_name: str) -> int:
        """
        Computes the bit-width of a variable.

        Args:
            var_name (str): The variable name.

        Returns:
            int: The bit-width of the variable.
        """

        if self._is_vector(var_name):
            # compute the length
            match = re.search('\[(\d+):(\d+)\]', var_name)  # [1:0]a
            l_bound = int(match.group(1))  # 1
            r_bound = int(match.group(2))  # 0
            return abs((l_bound - r_bound) + 1)
        else:
            return 1
