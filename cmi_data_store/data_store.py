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
    """
    Stores selected LLMs and interpreters with parameter configurations and messages of a conversation in a 
    JSON file with a current timestamp.
    """

    def __init__(self):
        print("Load Data Store ...")

    def write_file(self, key, data):
        """Write data to the JSON file. In the file's data, open key and append the given data to it."""

        with open(file,'r+') as f:
            file_data = json.load(f)
            file_data[key].append(data)
            f.seek(0)
            json.dump(file_data, f, indent = 4)

    def create_conversation(self):
        """Create a new JSON file with current timestamp for storing a new conversation."""

        global file
        global timestamp
        timestamp = str(int(time.time()))
        file = "cmi-" + timestamp + ".json"
        c = { LLM_CONFIG: [], INT_CONFIG: [], CONVERSATION: [] }
        with open(file,'w') as f:
            json.dump(c, f, indent = 4)

    def set_llm_configuration(self, selected_llm, llm_config):
        """Store the selected LLM with configuration parameters"""

        global last_llm
        global last_llm_config
        if last_llm != str(selected_llm) or last_llm_config != str(llm_config):
            last_llm = str(selected_llm)
            last_llm_config = str(llm_config)
            c = { TIMESTAMP:str(int(time.time())), LLM: selected_llm, LLM_CONFIG: llm_config }
            self.write_file(LLM_CONFIG, c)

    def set_interpreter_configuration(self, selected_int, int_config):
        """Store the selected interpreter with configuration parameters"""

        global last_int
        global last_int_config
        if last_int != str(selected_int) or last_int_config != str(int_config):
            last_int = str(selected_int)
            last_int_config = str(int_config)
            c = { TIMESTAMP:str(int(time.time())), INT: selected_int, INT_CONFIG: int_config }
            self.write_file(INT_CONFIG, c)

    def insert_prompt(self, prompt):
        """Store a user-provided prompt as part of the current conversaion"""

        c = { TIMESTAMP:str(int(time.time())), PROMPT: prompt }
        self.write_file(CONVERSATION, c)

    def insert_llm_response(self, response):
        """Store a LLM response as part of the current conversaion"""

        c = { TIMESTAMP:str(int(time.time())), PROMPT: response }
        self.write_file(CONVERSATION, c)

    def insert_interpreter_output(self, output):
        """Store an interpreter output as part of the current conversaion"""

        c = { TIMESTAMP:str(int(time.time())), PROMPT: output }
        self.write_file(CONVERSATION, c)
    