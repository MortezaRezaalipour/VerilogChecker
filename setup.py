from setuptools import setup, find_packages

setup(
    name="verilogChecker",  # Replace with your package name
    version="1.0.1",
    author="Morteza Rezaalipour",
    author_email="morteza.rezaalipour@usi.ch",
    description="A tool for synthesizing and evaluating Verilog circuits.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/MortezaRezaalipour/VerilogChecker",  # Replace with your GitHub repo
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "colorama",  # Add other dependencies if needed
    ],
    entry_points={
        "console_scripts": [
            "checker=checker.check:main",  # Replace with the actual entry point
        ]
    },
)
