# Equivalence Checker and Difference Evaluator

This utility has two operating modes: 
1. Equivalence Checking (enabled with the flag `--check`): designed to check the equivalence of two given circuits (in Verilog) based on the provided error threshold; if they are not equivalend, it will trigger an "ET beached!!!" message, otherwise, a "TEST -> PASS" is shown.
2. Difference Evaluation (enabled with the flag `--evaluate`): designed to evaluate the error of a given circuit (in Verilog). The output is "error=[errorValue]"


**Note: the error criteria can be computed based on different metrics such as Worst-Absolute Error, Mean Error Distance (MED), Mean-Squared Error Distance (MSED, Error Rate (ER), and Mean-Relative Error Distance (MRED)**

## Prerequisits

- Install the following tools:

1. **Linux**
2. **Yosys**: link (https://github.com/YosysHQ/yosys)
3. **Icarus Verilog**: link (https://github.com/steveicarus/iverilog)

**Note: add the binaries of 2 and 3 to your PATH**


## Folder Structure
- `./input/`: contains the input circuits to the tool. 
- `./input/exact/`: contains the exact circuits of our benchmark suite
- `./input/test/`: several approximate circuits generated by MECALS as a simple test
- `./report/`: in case of a breach to ET, a `.txt` file is dumped into this directory that includes the input combinations for which a breach of ET happend.
- `./temp`: all the intermediary files such as `yosys`, `iverilog`, and others are stored here.

## Usage

To run the checker, use the following syntax:


### Arguments

- `--input`, `-i`: Specify the path to the circuits to be checked. This option can be used multiple times to input multiple circuits.
- `--input_port_orders`, `-ipo`: Define the order of the input ports. This can be one of the predefined order types. The default is ['1', '1'].
- `--output_port_orders`, `-opo`: Define the order of the output ports similar to the input port orders. The default is ['1', '1'].
- `'--error_threshold'`, `-et`: Set the error threshold, which is an integer value. The default is `-1`.

`verifier.py` accepts the following command-line arguments to control its behavior and specify the parameters for the equivalence checking process:

- `--input`, `-i`:
  - **Description**: Specify the path(s) to the circuit file(s) that you want to check for equivalence. You can use this option multiple times if you need to input multiple circuit files.
  - **Usage Example**: `-i path/to/circuit1.v -i path/to/circuit2.v`
  
- `--input_port_orders`, `-ipo`:
  - **Description**: Define the order of the input ports. This determines how the input ports of the circuits are arranged and compared during the checking process.
  - **Choices**: `11`, `12`, `21`, `22`
  - **Default**: `['1', '1']`
  - **Usage Example**: `-ipo 21`
  
- `--output_port_orders`, `-opo`:
  - **Description**: Define the order of the output ports, similar to the input port orders. This affects how the output ports are arranged and compared.
  - **Choices**: `11`, `12`, `21`, `22`
  - **Default**: `['1', '1']`
  - **Usage Example**: `-opo 12`
  
- `--error_threshold`, `-et`:
  - **Description**: Set the error threshold, a float/int value that defines the acceptable error limit for the equivalence checking.
  - **Default**: `-1`
  - **Usage Example**: `-et 2.5`
  
- `--metric_type`, `-t`:
  - **Description**: Specify the metric type to use for evaluating the circuits' equivalence.
  - **Choices**: `wae` (Worst Average Error), `med` (Mean Error Distance), `msed` (Mean Squared Error Distance), `er` (Error Rate), `mred` (Maximum Relative Error Distance)
  - **Default**: `wae`
  - **Usage Example**: `-t msed`
  
- `--check`:
  - **Description**: Checks whether the two input Verilog circuits are equivalent within a specified error threshold. This mode is used to verify that the differences between the circuits fall within an acceptable range defined by the `--error_threshold` parameter.
  - **Usage Example**: `python3 checker.py -i path/to/circuit1.v -i path/to/circuit2.v -et 2 -t wae --check`
  
- `--evaluate`:
  - **Description**: Computes and reports the error between the two input circuits using the specified error metric. Available metrics are `wae` (Weighted Average Error), `med` (Median Error), `msed` (Mean Squared Error), `mred` (Maximum Relative Error Difference), and `er` (Error Rate). This mode is used for detailed analysis of how and where the circuits differ.
  - **Usage Example**: `python3 checker.py -i path/to/circuit1.v -i path/to/circuit2.v -et 0.5 -t med --evaluate`


### Port Orders

Assuming that an n-bit binary number X is represented as X = x<sub>n-1</sub>...x<sub>0</sub>,
Port orders define how the circuit ports are arranged in the checking process:


- **Input Order Types:**
  - `1`: [n:0]a, [n:0]b => circuit(a<sub>0</sub>, a<sub>1</sub>, ..., a<sub>n</sub>, b<sub>0</sub>, b<sub>1</sub>, ..., b<sub>n</sub>, [outputs])
  - `2`: [n:0]a, [n:0]b => circuit(a<sub>n</sub>, a<sub>n-1</sub>, ..., a<sub>0</sub>, b<sub>n</sub>, b<sub>n-1</sub>, ..., b<sub>0</sub>, [outputs])

- **Output Order Types:**
  - `1`: [n:0]y, [n:0]z => circuit([inputs], y<sub>0</sub>, y<sub>1</sub>, ..., y<sub>n</sub>, z<sub>0</sub>, z<sub>1</sub>, ..., z<sub>n</sub>)
  - `2`: [n:0]y, [n:0]z => circuit([inputs], y<sub>n</sub>, y<sub>n-1</sub>, ..., y<sub>0</sub>, z<sub>n</sub>, z<sub>n-1</sub>, ..., z<sub>0</sub>)

The order types are specified using numbers, where '1' and '2' define the specific arrangement of circuit pins.

- **Note: all exact files follow the order number 1 for both inputs and outputs** 


## Example 1

Here's an example command to run the verifier with specific input and output port orders:

- In this example, the approximate circuit is located in `./input/test/` directory and its name is `adder_i4_o3_wce1` (that supposed to have a WAE of 1).
The exact circuit is located in `./input/exact/` directory and its name is `adder_i4_o3.v`.
- The `-i` argument is used twice to specify two circuit files: `adder_i4_o3_wce1.v` and `adder_i4_o3.v`.
- The `-ipo` and `-opo` arguments set the input and output port orders respectively. Here, an `-ipo 21` (or `-opo 21`) means that the input order (output order) type of the first circuit is `2` and the second file is `1`.  
- The error threshold set is `1`. 



```bash
$ python3 checker_blahBlah.py -i  input/test/adder_i4_o3_wce1.v -i input/exact/adder_i4_o3.v -ipo 21 -opo 21 -et 1 -t wae --check
```

Upon running this command, you should get the following output:

```
args = An object of class Arguments:
self.circuits = ['input/test/adder_i4_o3_wce2.v', 'input/exact/adder_i4_o3.v']
self.input_port_orders = ['1', '2']
self.output_port_orders = ['1', '2']
self.metric_type = <function wae at 0x7fc0add399d0>
self.check = True
self.evaluate = False
self.et = 1.0

Exhaustive Simulation
Error Breached!!!

```

This means that at least, given this specific order, this circuit does not fulfill the error threshold it claims to have.


## Example 2

In this example, we will compute the error between two Verilog circuits using the Mean Squared Error (MSE) metric.

- Assume the approximate circuit is located in `./input/test/` directory and named `adder_i4_o3_wce2` (which has a different error characteristic).
- The exact circuit is in the `./input/exact/` directory, named `adder_i4_o3.v`.
- We use the `-i` argument twice to specify the two circuit files: `adder_i4_o3_wce2.v` and `adder_i4_o3.v`.
- The `-ipo` and `-opo` arguments set the input and output port orders respectively. In this case, `-ipo 12` and `-opo 12` set the port orders for both circuits respectively.
- We choose the Mean Squared Error (`msed`) as the metric type to evaluate the error between the circuits.

Here's the command to run the verifier in evaluate mode:

```bash
$ python3 checker_blahBlah.py -i input/test/adder_i4_o3_wce2.v -i input/exact/adder_i4_o3.v -ipo 12 -opo 12 -t msed --evaluate
```

Upon running this command, the output might look like:

```
args = An object of class Arguments:
self.circuits = ['input/test/adder_i4_o3_wce2.v', 'input/exact/adder_i4_o3.v']
self.input_port_orders = ['2', '1']
self.output_port_orders = ['2', '1']
self.metric_type = <function med at 0x7f8890272a60>
self.check = False
self.evaluate = True
self.et = -1

Exhaustive Simulation
error = 0.75
```

This output indicates the Mean Error Distance between the two specified circuits is 
