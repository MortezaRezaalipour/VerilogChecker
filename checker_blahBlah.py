from typing import List, Literal, Union, Dict
from synthesizer import Synthesizer
from verilog_processor import VerilogProcessor
from circuit import Circuit
import os
import subprocess
import random

# Constants for input/output orders
INPUT_ORDER_TYPE1 = "1"
INPUT_ORDER_TYPE2 = "2"
OUTPUT_ORDER_TYPE1 = "1"
OUTPUT_ORDER_TYPE2 = "2"


class Checker:
    def __init__(self,
                 exact_path: str,
                 approx_path: str,
                 input_order: List[str],
                 output_order: List[str],
                 metric: Literal["wae", "nmed", "med", "er"],
                 et: Union[float, int]) -> None:
        """
        Initializes the Checker with paths to two Verilog files (exact and approximate),
        input/output port orders, and comparison parameters.

        Args:
            exact_path (str): Path to the exact Verilog file.
            approx_path (str): Path to the approximate Verilog file.
            input_order (List[str]): Order of input ports for both circuits.
            output_order (List[str]): Order of output ports for both circuits.
            metric (Literal["wae", "nmed", "med", "er"]): Metric to use for comparison.
            et (Union[float, int]): Error tolerance for the comparison.
        """
        self.circuit1 = Circuit()
        self.circuit2 = Circuit()

        # Set paths and orders
        self.circuit1.path = exact_path
        self.circuit2.path = approx_path
        self.circuit1.input_order = input_order
        self.circuit2.input_order = input_order
        self.circuit1.output_order = output_order
        self.circuit2.output_order = output_order

        self.metric = metric
        self.et = et

        # Initialize synthesis tools
        self.verilog_processor = VerilogProcessor()
        self.synthesizer = Synthesizer(self.verilog_processor)

        print(f'Created directory')
        os.makedirs('Checker.bak', exist_ok=True)

        self._prepare_circuits()

    # ================== Helper Methods for Circuit Setup ==================

    def _prepare_circuits(self):
        """Synthesize both circuits and set up their properties."""
        self.circuit1.synth_path = f'temp/{self.circuit1.path}_syn.v'
        self.circuit2.synth_path = f'temp/{self.circuit2.path}_syn.v'

        name1, portlist1, input_dict1, output_dict1 = self.synthesizer.synthesize(self.circuit1.path)
        name2, portlist2, input_dict2, output_dict2 = self.synthesizer.synthesize(self.circuit2.path)

        self.circuit1.name, self.circuit2.name = name1, name2
        self.circuit1.input_dict, self.circuit2.input_dict = input_dict1, input_dict2
        self.circuit1.output_dict, self.circuit2.output_dict = output_dict1, output_dict2
        self.circuit1.input_count, self.circuit2.input_count = self.get_num_inputs(input_dict1), self.get_num_inputs(
            input_dict2)
        self.circuit1.output_count, self.circuit2.output_count = self.get_num_outputs(
            output_dict1), self.get_num_outputs(output_dict2)

        assert self.circuit1.input_count == self.circuit2.input_count, "Input counts are not equal"
        assert self.circuit1.output_count == self.circuit2.output_count, "Output counts are not equal"

    def get_num_inputs(self, input_dict: Dict) -> int:
        """Returns the bitwidth of the module's input."""
        return sum(width for _, width in input_dict.values())

    def get_num_outputs(self, output_dict: Dict) -> int:
        """Returns the bitwidth of the module's output."""
        return sum(width for _, width in output_dict.values())

    # ================== Simulation and Evaluation Methods ==================

    def simulate_and_evaluate(self, check: bool = False) -> Union[bool, float]:
        """Runs simulation and either checks equivalence or evaluates the circuits."""
        samples = self.generate_samples(self.circuit1.input_count)
        self.circuit1.simulation_pattern = samples
        self.circuit2.simulation_pattern = samples

        assert self.circuit1.simulation_pattern == self.circuit2.simulation_pattern, "Simulation patterns are not the same"

        # Simulate and import results
        self.simulate(self.circuit1)
        self.import_results(self.circuit1)
        self.simulate(self.circuit2)
        self.import_results(self.circuit2)

        # Perform check or evaluate
        if check:
            return self.check_circuits(self.circuit1, self.circuit2)
        else:
            return self.evaluate_circuits(self.circuit1, self.circuit2)

    def generate_samples(self, input_count: int) -> List[int]:
        """Generates simulation patterns based on the input count."""
        return list(range(2 ** input_count)) if input_count <= 10 else random.sample(range(0, 2 ** input_count), 1000)

    def simulate(self, circuit: Circuit):
        """Simulates a circuit by creating and running a testbench."""
        testbench = self.create_testbench(circuit, circuit.simulation_pattern)
        self.export_testbench(circuit.testbench_path, testbench)

        result_path = f'temp/{circuit.name}.txt'
        circuit.results_path = result_path
        self.run_testbench(circuit.testbench_path, circuit.synth_path, circuit.results_path)

    def import_results(self, circuit: Circuit):
        """Imports simulation results from the result path."""
        with open(circuit.results_path, 'r') as r1:
            circuit.simulation_output = r1.readlines()

    # ================== Testbench and Sample Generation ==================

    def create_testbench(self, circuit: Circuit, samples: List[int]) -> str:
        """Creates a testbench for a circuit."""
        module_signature = f'module {circuit.name}_tb;\n'
        input_dec = f'reg [{circuit.input_count - 1}:0] pi;\n'
        output_dec = f'wire [{circuit.output_count - 1}:0] po;\n'
        inst_dut = self.instantiate_dut(circuit)
        mapped_samples = f'initial\nbegin\n' + ''.join(
            self.integer_to_binary(circuit, sample) for sample in samples) + 'end\nendmodule\n'
        return module_signature + input_dec + output_dec + inst_dut + mapped_samples

    def instantiate_dut(self, circuit: Circuit) -> str:
        """Instantiates the DUT for a testbench."""
        dut_inst = f'{circuit.name} dut ('
        dut_inst += ', '.join(
            f'pi[{i}]' for i in range(circuit.input_count)) if circuit.input_order == INPUT_ORDER_TYPE1 else ', '.join(
            f'pi[{i}]' for i in reversed(range(circuit.input_count)))
        dut_inst += ', ' + ', '.join(f'po[{i}]' for i in range(
            circuit.output_count)) if circuit.output_order == OUTPUT_ORDER_TYPE1 else ', '.join(
            f'po[{i}]' for i in reversed(range(circuit.output_count)))
        return dut_inst + ');\n'

    def integer_to_binary(self, circuit: Circuit, sample: int) -> str:
        """Converts a sample integer to binary for testbench input."""
        binary_sample = self.integer_sample_to_binary(circuit, sample)
        return f"#1 pi={circuit.input_count}'b{binary_sample};\n#1 $display(\"%b\", po);\n"

    def integer_sample_to_binary(self, circuit: Circuit, sample: int) -> str:
        """Converts an integer sample to a binary string based on input order."""
        binary_sample = f'{sample:0{circuit.input_count}b}'
        return self.reorder_string(binary_sample) if circuit.input_order == INPUT_ORDER_TYPE2 else binary_sample

    def reorder_string(self, s: str) -> str:
        """Reorders a binary string for specific input orders."""
        mid = len(s) // 2
        return s[:mid][::-1] + s[mid:][::-1]

    # ================== Utility Methods ==================

    def export_testbench(self, output_path: str, testbench: str):
        """Exports a testbench to the specified path."""
        with open(output_path, 'w') as t:
            t.writelines(testbench)

    def run_testbench(self, testbench_path: str, dut_path: str, result_path: str):
        """Runs the testbench for a synthesized circuit using iverilog and vvp."""
        iverilog_command = f'iverilog -o temp/temp.iv {dut_path} {testbench_path}'
        vvp_command = 'temp/temp.iv'

        with open('temp/iverilog_log.txt', 'w') as f:
            subprocess.call(iverilog_command, shell=True, stdout=f)

        with open(result_path, 'w') as f:
            subprocess.call(['vvp', vvp_command], stdout=f)
