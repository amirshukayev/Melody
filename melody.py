#!/usr/bin/env python3
"""
Melody is a coding assistant that uses large language models
to help you debug and solve problems in a codebase.
"""

import subprocess
import re

from textwrap import dedent as d
from llm import Llm
from os import path

def readReadme():
    """
    Get the contents of a file called
    README.md in this directory
    """
    with open("README.md") as f:
        return f.read()

def readGitignore():
    """
    Get the globs in the gitignore file
    """
    with open(".gitignore") as f:
        lines = f.readlines()
    return [line.strip() for line in lines]

def get_project_name(llm, summary):
    """
    get project name from the summary
    """
    prompt = d(f'''
    From the following summary, what is the name of the project:
    Summary: {summary}
    Name:
    ''')
    return llm.generate_open_ai(prompt)[0]

class Melody:

    def __init__(self):
        self.pwd = './'
        self.cmd_re = re.compile(r'c:(bash|open|help) (.*)')

    def handle_bash(self, args):
        if args.split(' ')[0] == 'cd':
            self.pwd = path.join(self.pwd, args.split(' ')[1])
            return f'changed directory to {self.pwd}'
        else:
            return subprocess.check_output(args, shell=True)

    def handle_open(self, args):
        try:
            with open(path.join(self.pwd,args)) as f:
                return f.read()
        except Exception as e:
            return str(e)

    def handle_help(self, args):
        print(args)
        return input("Please enter response to Melody: ")

    def handle_help(self, args):
        pass

    def run_command(self, command):
        """
        run a command and return the output
        """
        for line in command.split('\n'):
            match = self.cmd_re.match(line.strip())

            if match:
                cmd = match.group(1)
                args = match.group(2)

                if cmd == 'bash':
                    return self.handle_bash(args)
                elif cmd == 'open':
                    return self.handle_open(args)
                elif cmd == 'help':
                    return self.handle_help(args)
            else:
                continue
        raise Exception("No command found")


    def run(self):
        objective = input("Objective: ")
        llm = Llm()

        # step 1a: determine the purporse of the project
        readme = readReadme()

        summary, _ = llm.summarize(readme)
        project_name = get_project_name(llm, summary)

        prompt_start = d(f'''
        You are a very careful programmer, working on the project {project_name}
        with the following readme: {summary}.

        You are currently working at the root directory of {project_name}.
        Your goal is to: {objective}
        Here are the tools: what is the first step you should take.
        ''')

        tools = d(f'''
        - c:bash <command>: you can issue bash commands and see the output. large outputs will be truncated
        - c:open <file>: you can open a file and see its contents
        - help <request>: you can ask a human an english-language question.

        Here are 3 examples of using the tools
        c:bash ls
        c:open main.py
        c:help what next step should i take to find the implementation of myFunction()
        ''')

        prompt_end = d(f'''
        Explain your thought process on what you should do next.
        Then output the command on a new line
        If you are unsure use c:help <question>

        example:
        thoughts: I will use c:bash ls to find the structure of the project
        c:bash ls

        now output your thoughts and command:

        ''')

        initial_prompt = prompt_start + tools + prompt_end

        OKGREEN = '\033[92m'
        ENDC = '\033[0m'

        prompt = initial_prompt

        text, _ = llm.generate_open_ai(prompt)
        print(text)
        command_results = self.run_command(text)

        while True:
            print(OKGREEN + prompt + ENDC)
            print(text)

            results_blob = d(f'''
            Results of the command are: {command_results}

            Output if you think it was a success or not, and what went wrong/correct
            Explain your thought process on what you should do next
            Then output the next command on a new line
            If you think you have the answer: output the answer, then output END on its own line
            ''')
            prompt = prompt + results_blob

            text, _ = llm.generate_open_ai(prompt)
            if text.split('\n')[-1].strip() == 'END':
                print(OKGREEN + prompt + ENDC)
                print(text)
                break

            command_results = self.run_command(text)

melody = Melody()
melody.run()
