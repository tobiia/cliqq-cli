import re
import os
import sys
import psutil
import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description="a simple, lightweight command line chat assistant to answer questions and carry out tasks on your computer
    )

    # Define the input argument
    parser.add_argument("input", help="The input file to process.")

    # Define the output argument
    parser.add_argument(
        "-o", "--output", help="The output file to save the results", required=True
    )

    # Parse the command-line arguments
    args = parser.parse_args()

    return parsed_args


def prep_prompt(prompt, path):
    op_sys = sys.platform
    shell = psutil.Process(os.getppid()).name()
    cwd = os.getcwd()

    with open(path) as fobj:
        prompt_template = fobj.read()
    prompt_template = re.sub(r"{OS}", op_sys, prompt_template)
    prompt_template = re.sub(r"{SHELL}", shell, prompt_template)
    prompt_template = re.sub(r"{CWD}", cwd, prompt_template)
    prompt_template = re.sub(r"{QUESTION}", prompt, prompt_template)
    return prompt_template
