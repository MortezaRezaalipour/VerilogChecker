from typing import List, Literal, Union, Dict, Tuple
from .synthesizer import Synthesizer
from .verilog import VerilogProcessor
from .circuit import Circuit
import os
import subprocess
import random
from colorama import Fore, Style
import colorama
colorama.init(autoreset=True)

INPUT_ORDER_TYPE1 = '1'  # [n:0]a, [n:0]b => circuit(a0, a1, ..., an, b0, b1, ..., bn, [outputs])
INPUT_ORDER_TYPE2 = '2'  # [n:0]a, [n:0]b => circuit(an, an-1, ..., a0, bn, bn-1, ..., b0, [outputs])

OUTPUT_ORDER_TYPE1 = '1'  # [n:0]y, [n:0]z => circuit([inputs], y0, y1, ..., yn, z0, z1, ..., zn)
OUTPUT_ORDER_TYPE2 = '2'  # [n:0]y, [n:0]z => circuit([inputs], yn, yn-1, ..., y0, zn, zn-1, ..., z0)

class Checker:
    def __init__(self,
                 exact_path: str,
                 approx_path: str,
                 input_order: List[str],
                 output_order: List[str],
                 metric: Literal["wae", "nmed", "med", "er"],
                 et: Union[float, int]  = float('inf'),
                 sample_count: int = 100) -> None:
        """
        Initializes the Checker with paths to two Verilog files (exact and approximate),
        input/output port orders, and comparison parameters.
        """
        self.circuit1 = Circuit()
        self.circuit2 = Circuit()

        # Set paths and orders
        self.circuit1.path = exact_path
        self.circuit2.path = approx_path
        self.circuit1.input_order = input_order[0]
        self.circuit2.input_order = input_order[1]
        self.circuit1.output_order = output_order[0]
        self.circuit2.output_order = output_order[1]
        self.sample_count = sample_count if sample_count else 100

        self.metric = metric
        self.et = et

        # Initialize synthesis tools
        self.verilog_processor = VerilogProcessor()
        self.synthesizer = Synthesizer(self.verilog_processor)

        # Set up a persistent `temp` directory
        self.temp_dir = "Checker.bak"
        os.makedirs(self.temp_dir, exist_ok=True)

        # Define paths for synthesized files
        exact_file_base_name = exact_path[:-2]
        approx_file_base_name = approx_path[:-2]
        self.circuit1.synth_path = os.path.join(self.temp_dir, f'{os.path.basename(exact_file_base_name)}_syn.v')
        self.circuit2.synth_path = os.path.join(self.temp_dir, f'{os.path.basename(approx_file_base_name)}_syn.v')

        # Prepare circuits for synthesis and simulation
        self._prepare_circuits()

    def _prepare_circuits(self):
        """Synthesize both circuits and set up their properties."""
        output_path1, name1, portlist1, input_dict1, output_dict1 = self.synthesizer.synthesize(self.circuit1.path, self.circuit1.synth_path)
        output_path2, name2, portlist2, input_dict2, output_dict2 = self.synthesizer.synthesize(self.circuit2.path, self.circuit2.synth_path)

        # Proceed if files exist, otherwise raise an error
        if not os.path.exists(self.circuit1.synth_path):
            raise FileNotFoundError(Fore.RED + f"Synthesis failed to create {self.circuit1.synth_path}")
        if not os.path.exists(self.circuit2.synth_path):
            raise FileNotFoundError(Fore.RED + f"Synthesis failed to create {self.circuit2.synth_path}")

        self.circuit1.name, self.circuit2.name = name1, name2
        self.circuit1.input_dict, self.circuit2.input_dict = input_dict1, input_dict2
        self.circuit1.output_dict, self.circuit2.output_dict = output_dict1, output_dict2
        self.circuit1.input_count = self.get_num_inputs(input_dict1)
        self.circuit2.input_count = self.get_num_inputs(input_dict2)
        self.circuit1.output_count = self.get_num_outputs(output_dict1)
        self.circuit2.output_count = self.get_num_outputs(output_dict2)

        assert self.circuit1.input_count == self.circuit2.input_count, "Input counts are not equal"
        assert self.circuit1.output_count == self.circuit2.output_count, "Output counts are not equal"

    def get_num_inputs(self, input_dict: Dict) -> int:
        """Returns the bitwidth of the module's input."""
        return sum(width for _, width in input_dict.values())

    def get_num_outputs(self, output_dict: Dict) -> int:
        """Returns the bitwidth of the module's output."""
        return sum(width for _, width in output_dict.values())

    def simulate(self, circuit: Circuit):
        """Simulates a circuit by creating and running a testbench."""
        print(Fore.BLUE + f'[I]: simulating started..')
        testbench = self.create_testbench(circuit, circuit.simulation_pattern)
        circuit.testbench_path = os.path.join(self.temp_dir, f'{circuit.name}_tb.v')
        self.export_testbench(circuit.testbench_path, testbench)
        circuit.results_path = os.path.join(self.temp_dir, f'{circuit.name}.txt')
        self.run_testbench(circuit.testbench_path, circuit.synth_path, circuit.results_path)

    def check(self) -> Tuple[Union[None, float, int], bool]:
        """Runs simulation and either checks equivalence or evaluates the circuits."""

        samples = self.generate_samples(self.sample_count)
        self.circuit1.simulation_pattern = samples
        self.circuit2.simulation_pattern = samples

        assert self.circuit1.simulation_pattern == self.circuit2.simulation_pattern, "Simulation patterns are not the same"

        self.simulate(self.circuit1)
        self.import_results(self.circuit1)
        self.simulate(self.circuit2)
        self.import_results(self.circuit2)

        return self.check_circuits(self.circuit1, self.circuit2)

    # ===================== For external use =======================
    @classmethod
    def Check(cls, exact_path: str,
                 approx_path: str,
                 input_order: List[str],
                 output_order: List[str],
                 metric: Literal["wae", "nmed", "med", "er"],
                 et: Union[float, int]  = float('inf'),
                 sample_count: int = 100):
        checker_obj = cls(exact_path, approx_path, input_order, output_order, metric, et)
        return checker_obj.check()

    def generate_samples(self, sample_count: int) -> List[int]:
        """Generates simulation patterns based on the input count."""
        print(Fore.BLUE + f'[I]: generating {sample_count} random samples...')
        return list(range(sample_count))

    def import_results(self, circuit: Circuit):
        """Imports simulation results from the result path."""
        with open(circuit.results_path, 'r') as r1:
            circuit.simulation_output = r1.readlines()

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
        dut_inst += ', '
        dut_inst += ', '.join(f'po[{i}]' for i in range(
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

    def export_testbench(self, output_path: str, testbench: str):
        """Exports a testbench to the specified path."""
        with open(output_path, 'w') as t:
            t.writelines(testbench)

    def run_testbench(self, testbench_path: str, dut_path: str, result_path: str):
        """Runs the testbench for a synthesized circuit using iverilog and vvp."""
        print(Fore.BLUE + f'[I]: running testbench {testbench_path}')
        iv_output_path = os.path.join(self.temp_dir, "temp.iv")
        iverilog_log_path = os.path.join(self.temp_dir, "iverilog_log.txt")

        if not os.path.exists(dut_path):
            print(Fore.RED + f"[E]: DUT file {dut_path} does not exist.")
        if not os.path.exists(testbench_path):
            print(Fore.RED + f"[E]: testbench file {testbench_path} does not exist.")

        iverilog_command = f'iverilog -o {iv_output_path} {dut_path} {testbench_path}'

        with open(iverilog_log_path, 'w') as f:
            subprocess.call(iverilog_command, shell=True, stdout=f)

        if not os.path.exists(iv_output_path):
            print(Fore.RED + f"[E]: iv output file {iv_output_path} was not created.")
            return

        with open(result_path, 'w') as f:
            subprocess.call(['vvp', iv_output_path], stdout=f)

    def check_circuits(self, circuit1: Circuit, circuit2: Circuit) -> Tuple[Union[None, float, int], bool]:
        """Performs an equivalence check between two circuits based on the specified metric."""
        error = self.calculate_metric(circuit1.simulation_output, circuit2.simulation_output)
        return error, error <= self.et

    def calculate_metric(self, result1: List[str], result2: List[str]) -> float:
        """Calculates the error metric between two sets of results based on the specified metric."""
        if self.metric == "wae":
            return self.wae(result1, result2)
        elif self.metric == "med":
            return self.med(result1, result2)
        elif self.metric == "er":
            return self.er(result1, result2)
        elif self.metric == "nmed":
            return self.mred(result1, result2)
        else:
            raise ValueError(Fore.RED + "[E]: unknown metric type")

    def wae(self, result1: List[str], result2: List[str]) -> int:
        """Calculates the Worst-Absolute Error (WAE) between two result sets."""
        return max(abs(int(a.strip(), 2) - int(b.strip(), 2)) for a, b in zip(result1, result2))

    def med(self, result1: List[str], result2: List[str]) -> float:
        """Calculates the Mean-Error Distance (MED) between two result sets."""
        return sum(abs(int(a.strip(), 2) - int(b.strip(), 2)) for a, b in zip(result1, result2)) / len(result1)

    def er(self, result1: List[str], result2: List[str]) -> float:
        """Calculates the Error Rate (ER) between two result sets."""
        unequal_count = sum(1 for a, b in zip(result1, result2) if a != b)
        return (unequal_count / len(result1)) * 100

    def mred(self, result1: List[str], result2: List[str]) -> float:
        """Calculates the Mean-Relative Error Distance (MRED) between two result sets."""
        relative_errors = [
            abs(int(a.strip(), 2) - int(b.strip(), 2)) / max(int(a.strip(), 2), 1)
            for a, b in zip(result1, result2)
        ]
        return (sum(relative_errors) / len(relative_errors)) * 100
