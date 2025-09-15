import re
import os
import sys
import psutil


def prep_prompt(prompt):
    op_sys = sys.platform
    shell = psutil.Process(os.getppid()).name()
    cwd = os.getcwd()

    with open("template.txt") as fobj:
        prompt_template = fobj.read()
    prompt_template = re.sub(r"{OS}", op_sys, prompt_template)
    prompt_template = re.sub(r"{SHELL}", shell, prompt_template)
    prompt_template = re.sub(r"{CWD}", cwd, prompt_template)
    prompt_template = re.sub(r"{QUESTION}", prompt, prompt_template)
    return prompt_template
