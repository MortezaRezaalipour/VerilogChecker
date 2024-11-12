import tempfile
import subprocess
import os
from typing import Tuple, Optional
from .verilog import *

class Synthesizer:
    def __init__(self, verilog_processor: VerilogProcessor):
        """
        This class is responsible for synthesizing Verilog files using Yosys, managing temporary files,
        and handling necessary preprocessing steps through an instance of VerilogProcessor.
        """
        self.verilog_processor = verilog_processor  # Instance of Verilog class
    def synthesize(self, input_path: str) -> Tuple[str, Tuple[str, list, dict, dict]]:
        """
        Synthesizes a Verilog file using Yosys, creating a temporary output file.

        Args:
            input_path (str): The path to the input Verilog file to be synthesized.

        Returns:
            Tuple[str, Tuple]: The path to the synthesized output file and the renaming details.

        Raises:
            Exception: If Yosys encounters an error during synthesis.
        """
        self.verilog_processor._fix_module_name(input_path)

        # Create a temporary file to store the synthesized output
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".v")
        output_path = temp_file.name

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
        process = subprocess.run(['yosys', '-p', yosys_command], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        if process.stderr.decode():
            print("Error!")
            raise Exception(f'ERROR! Yosys encountered an issue with {input_path}\n{process.stderr.decode()}')

        # Close the temporary file handle to ensure it’s saved
        temp_file.close()

        # Rename variables in the synthesized output
        renaming_details = self.verilog_processor._rename_variables(output_path, output_path)

        return output_path, renaming_details

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