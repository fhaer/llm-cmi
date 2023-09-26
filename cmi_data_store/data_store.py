import sys
import json
import time
import uuid

CONVERSATION = "conversation"

LLM = "llm"
LLM_CONFIG = "llm_configuration"
LLM_CONFIG_LIST = "llm_configurations"

INT = "interpreter"
INT_CONFIG = "int_configuration"
INT_CONFIG_LIST = "int_configurations"

PROMPT = "user_prompt"
RESPONSE = "llm_response"
INTERPRETER = "int_output"

MESSAGE_ID = "message_id"
TIMESTAMP = "timestamp"

class DataStore:
    """
    Stores selected LLMs and interpreters with parameter configurations and messages of a conversation in a 
    JSON file with a current timestamp.
    """

    def __init__(self):
        print("Load Data Store ...")
        self.file = None
        self.timestamp = None
        self.message_id = 0
        self.last_llm = ""
        self.last_llm_config = ""
        self.last_int = ""
        self.last_int_config = ""

    def write_file(self, key, data):
        """Write data to the JSON file. In the file's data, open key and append the given data to it."""

        with open(self.file,'r+') as f:
            file_data = json.load(f)
            file_data[key].append(data)
            f.seek(0)
            json.dump(file_data, f, indent = 4)

    def create_conversation(self):
        """Create a new JSON file with current timestamp for storing a new conversation."""

        self.timestamp = int(time.time())
        self.file = "cmi-" + str(uuid.uuid1()) + ".json"
        c = { LLM_CONFIG_LIST: [], INT_CONFIG_LIST: [], CONVERSATION: [] }
        with open(self.file,'w') as f:
            json.dump(c, f, indent = 4)

    def set_llm_configuration(self, selected_llm, llm_config):
        """Store the selected LLM with configuration parameters"""

        if self.last_llm != str(selected_llm) or self.last_llm_config != str(llm_config):
            self.last_llm = str(selected_llm)
            self.last_llm_config = str(llm_config)
            next_message_id = self.message_id + 1
            c = { TIMESTAMP:int(time.time()), MESSAGE_ID: next_message_id, LLM: selected_llm, LLM_CONFIG: llm_config }
            self.write_file(LLM_CONFIG_LIST, c)

    def set_interpreter_configuration(self, selected_int, int_config):
        """Store the selected interpreter with configuration parameters"""

        if self.last_int != str(selected_int) or self.last_int_config != str(int_config):
            self.last_int = str(selected_int)
            self.last_int_config = str(int_config)
            next_message_id = self.message_id + 1
            c = { TIMESTAMP:int(time.time()), MESSAGE_ID: next_message_id, INT: selected_int, INT_CONFIG: int_config }
            self.write_file(INT_CONFIG_LIST, c)

    def insert_prompt(self, prompt):
        """Store a user-provided prompt as part of the current conversaion"""
        
        self.message_id += 1
        c = { TIMESTAMP:int(time.time()), MESSAGE_ID: self.message_id, PROMPT: prompt }
        self.write_file(CONVERSATION, c)

    def insert_llm_response(self, response):
        """Store a LLM response as part of the current conversaion"""

        self.message_id += 1
        c = { TIMESTAMP:int(time.time()), MESSAGE_ID: self.message_id, RESPONSE: response }
        self.write_file(CONVERSATION, c)

    def insert_interpreter_output(self, output):
        """Store an interpreter output as part of the current conversaion"""

        self.message_id += 1
        c = { TIMESTAMP:int(time.time()), MESSAGE_ID: self.message_id, INTERPRETER: output }
        self.write_file(CONVERSATION, c)
    