from typing import List, Union, Dict, Iterable, Any, Literal, Tuple
from .circuit import Circuit
from colorama import Fore, Style
import colorama
colorama.init(autoreset=True)
import os
import re
import subprocess
import tempfile
from tempfile import mkstemp
from shutil import move, copymode
from collections import OrderedDict
from .synthesizer import Synthesizer
from .verilog import VerilogProcessor

class Checker():
    """
    Initializes the Checker with paths to two Verilog files (exact and approximate),
    a metric for comparison, and an error tolerance.

    Args:
        path1 (str): Path to the exact Verilog file.
        path2 (str): Path to the approximate Verilog file.
        metric (Literal["wae", "nmed", "med", "er"]): Metric to use for comparison.
        et (Union[float, int]): Error tolerance for the comparison.
        sample_count (int, optional): Number of samples to use in simulations.
    """
    def __init__(self, path1: str, path2: str, metric: Literal["wae", "nmed", "med", "er"], et: Union[float, int], sample_count: int = None) -> None:
        self.path1 = path1
        self.path2 = path2
        self.metric = metric
        self.et = et
        self.sample_count = 100 if sample_count is None else sample_count
        # synthesize both circuits and remember their address

        # Initialize VerilogProcessor and Synthesizer
        self.verilog_processor = VerilogProcessor()
        self.synthesizer = Synthesizer(self.verilog_processor)

        # Synthesize both circuits and store the paths to the synthesized files
        self.synthesized_path1, _ = self.synthesizer.synthesize(self.path1)
        self.synthesized_path2, _ = self.synthesizer.synthesize(self.path2)
    @property
    def exact(self):
        return self.path1

    @property
    def approximate(self):
        return self.path2

    def synthezied_exact(self):
        return self.synthesized_path1

    def synthesized_approximate(self):
        return self.synthesized_path2

    def check(self) -> Tuple[Union[bool, None], Union[float, int]]:

        """
        Runs a check between the exact and approximate circuits by simulating them
        and calculating the error based on the specified metric and error tolerance.

        Returns:
            Tuple[Union[bool, None], Union[float, int]]: A tuple containing a boolean
            indicating if the error is within tolerance, and the calculated error.
        """

        # create two circuits
        # synthesize them
        # simulate them
        # get their error
        pass


    def __repr__(self):
        return (f'Check({self.path1},'
                f' {self.path2},'
                f' {self.metric},'
                f' {self.et})')

    # ============FOR USE AS A PYPI PACKAGE==================
    @classmethod
    def Check(cls, path1: str, path2: str, metric: Literal["wae", "nmed", "med", "er"], et: Union[float, int]) -> Tuple[
        Union[bool, None], Union[float, int]]:
        print(f'Not implemented yet')
        raise NotImplementedError
        pass

