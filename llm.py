#!/usr/bin/env python3

from cohere import Client as Co
import openai
from os import environ, path
from datetime import datetime
import json

cohere_api_key = environ.get("COHERE_API_KEY")
co = Co(cohere_api_key)

class Calls:
    def __init__(self, t, model, temp, prompt, res):
        self.t = t
        self.model = model
        self.temp = temp
        self.prompt = prompt
        self.res = res

        if t == 'generate':
            self.text = res.generations[0].text
        elif t == 'summarize':
            self.text = res.summary
        elif t == 'chat_complete':
            self.text = res.choices[0].message.content
        elif t == 'complete':
            self.text = res.choices[0].text

    def __str__(self):
        """
        Convert Call to a dumpable string
        """
        obj = {
            "prompt": self.prompt,
            "text": self.text,
            "model": self.model,
            "temp": self.temp,
            "time": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        pretty = json.dumps(obj, indent=2)
        return str(pretty)


class Llm:

    def __init__(self):
        """
        This class handles LLM calls and writes them to a log
        """
        self.calls = []
        self.gen_model = 'xlarge'
        self.summarize_model = 'summarize-xlarge'
        self.temperature = 0.6

        self.init_log()

    def init_log(self):
        """
        Keeps a buffer of logs and position written to file
        """
        self.log = []
        self.log_dir = path.join(path.expanduser('~'), '.melody', 'logs')
        self.date = datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
        self.log_file = self.log_dir + self.date + '.json'
        # keep track of next index in log file we need to write to disk
        self.write_pos = 0

    def generate_open_ai(self, prompt):
        """
        This function runs a generate call with open ai's model
        """
        model = 'text-davinci-003'
        res = openai.Completion.create(
            model=model,
            prompt=prompt,
            temperature=self.temperature,
            max_tokens=3000
        )

        call = Calls('complete', model, self.temperature, prompt, res)
        self.log.append(call)
        self.flush_log()

        return call.text, call

    def generate(self, prompt):
        """
        This function runs a complete prompt using the cohere API
        """
        model = self.gen_model
        res = co.generate(
            prompt=prompt,
            model=model,
            temperature=self.temperature)

        call = Calls('generate', model, self.temperature, prompt, res)
        self.log.append(call)
        self.flush_log()

        return call.text, call

    def summarize(self, text):
        """
        This function runs a complete prompt using the cohere API
        """
        model = self.summarize_model
        res = co.summarize(
            length='short',
            text=text,
            model=model,
            temperature=self.temperature)

        call = Calls('summarize', model, self.temperature, text, res)
        self.log.append(call)
        self.flush_log()

        return call.text, call

    def flush_log(self):
        """
        Flush the log to disk
        """
        for item in self.log[self.write_pos:]:
            with open(self.log_file, 'a+') as f:
                f.write(str(item) + '\n')

        self.write_pos = len(self.log)
