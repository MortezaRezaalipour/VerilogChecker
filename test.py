import sys
from checker.check import Checker  # Import Checker only


def main():
    if len(sys.argv) < 3:
        print("Usage: python test.py <exact_verilog_path> <approximate_verilog_path>")
        sys.exit(1)

    exact_verilog_path = sys.argv[1]
    approximate_verilog_path = sys.argv[2]

    # Initialize the Checker with test parameters
    checker = Checker(
        path1=exact_verilog_path,
        path2=approximate_verilog_path,
        metric="wae",  # Example metric, adjust as needed
        et=0.05  # Example error tolerance, adjust as needed
    )

    # Access synthesized file paths and perform checks
    print("Synthesis for exact circuit path:", checker.exact)
    print("Synthesis for approximate circuit path:", checker.approximate)

    # Perform the check (Placeholder, as `check` method is not fully implemented)
    try:
        result = checker.check()
        print("Check result:", result)
    except NotImplementedError:
        print("Check method is not implemented yet.")


if __name__ == '__main__':
    main()
