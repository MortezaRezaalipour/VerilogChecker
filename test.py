import sys
from checker.check import Checker  # Import Checker only


def main():
    if len(sys.argv) < 3:
        print("Usage: python test.py <exact_verilog_path> <approximate_verilog_path>")
        sys.exit(1)

    exact_verilog_path = sys.argv[1]
    approximate_verilog_path = sys.argv[2]

    input_order = ["1", "1"]  # Example input order; adjust as needed
    output_order = ["1", "1"]  # Example output order; adjust as needed
    metric = "wae"  # Example metric
    error_tolerance = 5  # Example error tolerance

    # Initialize the Checker with test parameters
    checker = Checker(
        exact_path=exact_verilog_path,
        approx_path=approximate_verilog_path,
        input_order=input_order,
        output_order=output_order,
        metric=metric,
        # et=error_tolerance
    )

    # Perform the check

    error, flag = checker.check()
    print(f'{error}, {flag}')


    print(Checker.Check(
        exact_path=exact_verilog_path,
        approx_path=approximate_verilog_path,
        input_order=input_order,
        output_order=output_order,
        metric=metric,
        # et=error_tolerance
    ))
if __name__ == '__main__':
    main()
