import tempfile
import subprocess
import os
from typing import Tuple, Optional, Any
from .verilog import *

class Synthesizer:
    def __init__(self, verilog_processor: VerilogProcessor):
        """
        This class is responsible for synthesizing Verilog files using Yosys, managing temporary files,
        and handling necessary preprocessing steps through an instance of VerilogProcessor.
        """
        self.verilog_processor = verilog_processor  # Instance of Verilog class
    def synthesize(self, input_path: str, output_path: str) -> Tuple[str, Any, Any, Any, Any]:
        """
        Synthesizes a Verilog file using Yosys, creating a temporary output file.

        Args:
            input_path (str): The path to the input Verilog file to be synthesized.

        Returns:
            Tuple[str, Tuple]: The path to the synthesized output file and the renaming details.

        Raises:
            Exception: If Yosys encounters an error during synthesis.
        """
        print(Fore.BLUE + f'[I: synthesizing {input_path}]')
        self.verilog_processor._fix_module_name(input_path)

        # Create a temporary file to store the synthesized output
        # temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".v")
        # Yosys synthesis command
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

        # Run Yosys with the synthesis command
        # process = subprocess.run(['yosys', '-p', yosys_command], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        # if process.stderr.decode():
        #     print("Error!")
        #     raise Exception(f'ERROR! Yosys encountered an issue with {input_path}\n{process.stderr.decode()}')
        #

        process = subprocess.run(['yosys', '-p', yosys_command], stderr=subprocess.PIPE, stdout=subprocess.PIPE)

        # Debugging: Output Yosys logs for errors
        if process.stderr:
            print("Yosys synthesis error output:")
            print(process.stderr.decode())

        # Check if the file was created
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Yosys synthesis failed to create output file: {output_path}")

        # Close the temporary file handle to ensure it’s saved


        # Rename variables in the synthesized output
        module_name, port_list, new_input_dict, output_dict = self.verilog_processor._rename_variables(output_path, output_path)

        return output_path, module_name, port_list, new_input_dict, output_dict

    def cleanup(self, path: str) -> Optional[None]:
        """
        Deletes a specified file, typically used to remove temporary synthesized files.

        Args:
            path (str): The path to the file to be deleted.
        """
        try:
            os.remove(path)
        except FileNotFoundError:
            print(f"Warning: File {path} already removed or not found.")