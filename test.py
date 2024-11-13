from checker.check import *
import sys
import re

def test():
    exact_path = sys.argv[1]
    approx_path = sys.argv[2]

    wce = re.search('wc(\d+)', approx_path).group(1)
    error, flag = Checker.Check(
        exact_path = exact_path,
        approx_path = approx_path,
        input_order= ['1', '1'],
        output_order= ['1', '1'],
        metric='wae',
        et = int(wce)

    )

    print(f'{error}, {flag}')


if __name__ == '__main__':
    test()