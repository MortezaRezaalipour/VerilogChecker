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
                buffer = ""  # Buffer to collect multiline module declarations
                inside_module = False  # Flag to indicate we're reading a module

                for line in old_file:
                    if 'module' in line and 'endmodule' not in line:
                        inside_module = True  # Start buffering
                        buffer += line

                    elif inside_module:
                        buffer += line  # Keep adding lines to the buffer
                        if ");" in line:  # Found the end of the module declaration
                            # Apply regex to the complete buffered module declaration
                            pattern = r'(module )([^\(]+)(\(.*?\);)'

                            match = re.search(pattern, buffer, flags=re.DOTALL)
                            if match:
                                second = match.group(2)  # Extract the module name
                                # Replace the module name with `subst`
                                buffer = buffer.replace(second, subst)
                            new_file.write(buffer)  # Write the modified buffer
                            buffer = ""  # Reset buffer
                            inside_module = False  # Exit module context

                    else:
                        new_file.write(line)  # Write non-module lines as-is

        # Replace the old file with the new one
        # copymode(input_path, abs_path)
        # os.remove(input_path)
        # move(abs_path, input_path)
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

        verilog_str_tmp = verilog_str


        module_name, port_list = self._extract_module_signature(verilog_str_tmp)

        input_dict, output_dict = self._extract_inputs_outputs( verilog_str, port_list)

        new_labels = self._create_new_labels(port_list, input_dict, output_dict)


        # verilog_str = verilog_str.split('\n')
        verilog_str = self._relabel_nodes(verilog_str, new_labels)

        with open(f'{output_path}', 'w') as outfile:
            outfile.write(f'{verilog_str}\n')

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
        # if re.search('mul_i12_o12_lac0_20241113', input_path):
        #     exit()
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
        for i_idx in input_dict.keys():
            i = input_dict[i_idx][0]
            if i in port_list:
                p_idx = port_list.index(i)
                new_labels[i] = f'in{p_idx}'

        for o_idx in output_dict.keys():
            o = output_dict[o_idx][0]
            if o in port_list:
                p_idx = port_list.index(o)
                new_labels[o] = f'out{p_idx - (len(input_dict))}'

        return new_labels

    def _relabel_nodes(self, verilog_str: str, new_labels: dict) -> str:
        """
        Relabels variables in a Verilog string based on new_labels mapping.

        Args:
            verilog_str (str): The Verilog code as a single string.
            new_labels (dict): A dictionary mapping old variable names to new labels.

        Returns:
            str: The Verilog string with relabeled variables.
        """
        # Use a regex pattern to replace all labels
        def replace_match(match):
            old_label = match.group(0)
            return new_labels.get(old_label, old_label)  # Replace if found, else keep original

        # Construct a regex to match any of the keys in new_labels
        pattern = re.compile(r'\b(?:' + '|'.join(map(re.escape, new_labels.keys())) + r')\b')

        # Replace all matches using the pattern
        relabeled_verilog = pattern.sub(replace_match, verilog_str)

        return relabeled_verilog

    # def _relabel_nodes(self, verilog_str: List[str], new_labels: Dict):
    #     """
    #     Replaces old variable names with new labels in the Verilog code.
    #
    #     Args:
    #         verilog_str (List[str]): Lines of Verilog code.
    #         new_labels (Dict): Dictionary mapping old names to new labels.
    #
    #     Returns:
    #         List[str]: Modified Verilog code with relabeled nodes.
    #     """
    #     verilog_str_tmp = verilog_str
    #     print(f'{verilog_str = }')
    #     for line_idx, line in enumerate(verilog_str):
    #         for key, value in new_labels.items():
    #
    #             escaped_key = re.escape(key)
    #             if re.search(f'{escaped_key}[,;)\s\n\r]|({escaped_key})$', line):
    #                 found = re.search(f'({escaped_key})[,;)\s\r\n]|({escaped_key})$', line)
    #                 middle = found.group(1)
    #                 end = found.group(2)
    #
    #                 s = found.span()[0]
    #                 if found.group(1):
    #                     e = s + len(found.group(1))
    #                     line = f"{line[:s]}{value}{line[e:]}"
    #                 elif found.group(2):
    #                     line = f"{line[:s]}{value}"
    #                 else:
    #                     print(
    #                         Fore.RED + f'ERROR! in (__name__): variable{key} does not belong in either of the two groups!' + Style.RESET_ALL)
    #                 verilog_str_tmp[line_idx] = line
    #     return verilog_str_tmp
    def _buffer_signature(self, verilog_str: str) -> str:
        """
        Buffers content from 'module' to the first ');' in the Verilog code string.

        Args:
            verilog_code (str): Verilog code as a single string.

        Returns:
            str: The complete module declaration as a single string.
        """
        buffer = ""  # To accumulate lines
        inside_module = False  # Flag to detect when we're inside the module declaration

        for line in verilog_str.splitlines():  # Split the single string into lines
            line = line.strip()  # Remove leading and trailing spaces

            # Check if the line starts with 'module' (beginning of the declaration)
            if line.startswith("module"):
                inside_module = True  # Start buffering
                buffer += line + " "  # Add the line to the buffer
            elif inside_module:
                buffer += line + " "  # Continue buffering
                if ");" in line:  # Check if the module declaration ends
                    break  # Exit the loop once the module declaration is complete

        return buffer.strip()

    def _extract_module_signature(self, verilog_str: str) -> Tuple[str, List[str]]:
        """
        Extracts the module name and port list from the Verilog file.

        Args:
            verilog_str (List[str]): Lines of Verilog code.

        Returns:
            Tuple[str, List[str]]: The module name and list of port names.
        """
        module_name = ''
        port_list = []
        buffer = self._buffer_signature(verilog_str)

        match = re.match(r'^module\s+([\w\\]+)\s*\(', buffer)
        if match:
            module_name = match.group(1)  # Group 1 captures the module name
        else:
            raise ValueError(Fore.RED + "Failed to extract module name. Invalid module declaration.")

        match = re.search(r'\(([^)]*)\)\s*;', buffer, flags=re.DOTALL)
        if match:
            ports_str = match.group(1)  # Extract the content inside parentheses
            # Split ports by comma and remove leading/trailing whitespace
            port_list = [port.strip() for port in ports_str.split(',') if port.strip()]
        else:
            raise ValueError(Fore.RED + "Failed to extract port list. Invalid module declaration.")
        return module_name, port_list

    def _extract_inputs_outputs(self, verilog_str, port_list):
        """
        Extracts inputs and outputs from the Verilog code based on the port list.

        Args:
            verilog_str (Union[str, List[str]]): Verilog code as a string or list of lines.
            port_list (List[str]): List of module ports.

        Returns:
            Tuple[Dict[str, str], Dict[str, str]]: Input and output dictionaries.
        """
        # Ensure verilog_str is a string
        if isinstance(verilog_str, list):
            verilog_str = " ".join(line.strip() for line in verilog_str)


        # Extract input and output declarations
        input_decl = re.findall(r'input\s+([^;]+);', verilog_str)
        output_decl = re.findall(r'output\s+([^;]+);', verilog_str)



        # Process declarations into individual ports
        input_ports = []
        for decl in input_decl:
            split_ports = [port.strip() for port in re.split(r'[,\s]+', decl) if port.strip()]
            input_ports.extend(split_ports)

        output_ports = []
        for decl in output_decl:
            split_ports = [port.strip() for port in re.split(r'[,\s]+', decl) if port.strip()]
            output_ports.extend(split_ports)


        # convert them into dictionary
        port_dict = {}

        for p_idx, p in enumerate(port_list):
            port_dict[p] = p_idx

        input_dict = {}
        for i_idx, i in enumerate(input_ports):
            if i in port_dict:
                input_dict[port_dict[i]] = (i, 1)

        output_dict = {}
        for o_idx, o in enumerate(output_ports):
            if o in port_dict:

                output_dict[port_dict[o]] = (o, 1)


        return input_dict, output_dict

    # def _extract_inputs_outputs(self, verilog_str: List[str], port_list: List[str]):
    #     """
    #     Extracts inputs and outputs from the Verilog code.
    #
    #     Args:
    #         verilog_str (List[str]): Lines of Verilog code.
    #         port_list (List[str]): List of ports in the module.
    #
    #     Returns:
    #         Tuple[Dict[int, Tuple[str, int]], Dict[int, Tuple[str, int]]]: Dictionaries for input and output ports.
    #     """
    #     input_dict: Dict[int:(str, int)] = {}
    #     output_dict: Dict[int:(str, int)] = {}
    #     # example:
    #     # for module circuit(a, b, c, d)
    #     # input [1:0] a;
    #     # input [2:0]b;
    #     # output d;
    #     # output [3:0]c;
    #     # example input_dict = {0:(a, 2), 1:(b, 3)}
    #     # example input_dict = {3:(d, 1), 2:(c, 3)}
    #
    #     for line in verilog_str:
    #         line = line.strip()  # remove all whitespaces at the beginning or end of the line
    #         # extract inputs
    #         if line.startswith('input'):
    #             match_obj = re.search('input (.+)', line)  # input a, b, c; or input [1:0] a;
    #             cur_input_str = match_obj.group(1)  # a, b, c or [1:0] a
    #             cur_input_list = cur_input_str.strip().replace(" ", "").split(',')  # ['a', 'b', 'c'] or ['[1:0]a']
    #             cur_input_list = self._check_multi_vector_declaration(cur_input_list)
    #             for inp in cur_input_list:
    #
    #                 if self._get_name(inp) in port_list:
    #                     position_in_module_signature = port_list.index(self._get_name(inp))
    #                     input_dict[position_in_module_signature] = (self._get_name(inp), self._get_width(inp))
    #                 else:
    #
    #                     raise Exception(f"input name {self._get_name(inp)} is not in the port_list {port_list}")
    #         # extract outputs
    #         if line.startswith('output'):
    #             match_obj = re.search('output (.+)', line)  # input a, b, c; or input [1:0] a;
    #             cur_output_str = match_obj.group(1)  # a, b, c or [1:0] a
    #             cur_output_list = cur_output_str.strip().replace(" ", "").split(',')  # ['a', 'b', 'c'] or ['[1:0]a']
    #             cur_output_list = self._check_multi_vector_declaration(cur_output_list)
    #             for out in cur_output_list:
    #                 if self._get_name(out) in port_list:
    #                     position_in_module_signature = port_list.index(self._get_name(out))
    #                     output_dict[position_in_module_signature] = (self._get_name(out), self._get_width(out))
    #                 else:
    #                     raise Exception(f"output name {self._get_name(out)} is not in the port_list")
    #         sorted_input_dict = OrderedDict(sorted(input_dict.items()))
    #         sorted_output_dict = OrderedDict(sorted(output_dict.items()))
    #     return input_dict, output_dict

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
