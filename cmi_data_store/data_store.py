import sys
import json
import time
import os

file = None
timestamp = None

last_llm = ""
last_llm_config = ""

last_int = ""
last_int_config = ""

CONVERSATION = "conversation"

LLM = "llm"
LLM_CONFIG = "llm_configuration"

INT = "interpreter"
INT_CONFIG = "int_configuration"

PROMPT = "user_prompt"
RESPONSE = "llm_response"
INTERPRETER = "interpreter_output"

TIMESTAMP = "timestamp"

class DataStore:

    def __init__(self):
        print("Load Data Store ...")

    def write_file(self, key, data):
        with open(file,'r+') as f:
            file_data = json.load(f)
            file_data[key].append(data)
            f.seek(0)
            json.dump(file_data, f, indent = 4)

    def create_conversation(self):
        global file
        global timestamp
        timestamp = str(int(time.time()))
        file = "cmi-" + timestamp + ".json"
        c = { LLM_CONFIG: [], INT_CONFIG: [], CONVERSATION: [] }
        with open(file,'w') as f:
            json.dump(c, f, indent = 4)

    def set_llm_configuration(self, selected_llm, llm_config):
        global last_llm
        global last_llm_config
        if last_llm != str(selected_llm) or last_llm_config != str(llm_config):
            last_llm = str(selected_llm)
            last_llm_config = str(llm_config)
            c = { TIMESTAMP:str(int(time.time())), LLM: selected_llm, LLM_CONFIG: llm_config }
            self.write_file(LLM_CONFIG, c)

    def set_interpreter_configuration(self, selected_int, int_config):
        global last_int
        global last_int_config
        if last_int != str(selected_int) or last_int_config != str(int_config):
            last_int = str(selected_int)
            last_int_config = str(int_config)
            c = { TIMESTAMP:str(int(time.time())), INT: selected_int, INT_CONFIG: int_config }
            self.write_file(INT_CONFIG, c)

    def insert_prompt(self, prompt):
        c = { TIMESTAMP:str(int(time.time())), PROMPT: prompt }
        self.write_file(CONVERSATION, c)

    def insert_llm_response(self, response):
        c = { TIMESTAMP:str(int(time.time())), PROMPT: response }
        self.write_file(CONVERSATION, c)

    def insert_interpreter_output(self, output):
        c = { TIMESTAMP:str(int(time.time())), PROMPT: output }
        self.write_file(CONVERSATION, c)
    