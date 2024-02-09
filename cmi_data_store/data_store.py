import os
import json
import time
import datetime as dt
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
INT_INPUT = "int_input"
INT_OUTPUT = "int_output"
MESSAGE = "message"
INIT_MESSAGE = "init_message"
EXEC_DURATION_S = "execution_duration_s"

MESSAGE_ID = "message_id"
TIMESTAMP = "timestamp"

DIRECTORY = "cmi_logs"

class DataStore:
    """
    Stores selected LLMs and interpreters with parameter configurations and messages of a conversation in a 
    JSON file with a current timestamp.
    """

    def __init__(self):
        print("Load Data Store ...")
        self.directory = None
        self.log_file = None
        self.timestamp = None
        self.conversation_id = ""
        self.init_message = ""
        self.message_id = 0
        self.last_llm = ""
        self.last_llm_config = ""
        self.last_int = ""
        self.last_int_config = ""

    def initialize_log_file(self):
        """Creates a new file."""
        c = {
            LLM_CONFIG_LIST: [],
            INT_CONFIG_LIST: [],
            CONVERSATION: []
        }

        os.makedirs(self.directory, exist_ok=True)
        with open(self.log_file, 'w') as f:
            json.dump(c, f, indent=4)

    def write_log_file(self, key, data):
        """Write data to the JSON file. In the file's data, open key and append the given data to it."""

        if not os.path.isfile(self.log_file):
            self.initialize_log_file()

        with open(self.log_file, 'r+') as f:
            file_data = json.load(f)
            file_data[key].append(data)
            f.seek(0)
            json.dump(file_data, f, indent=4)

    def get_timestamp(self):
        return dt.datetime.now().strftime("%y%m%d-%H%M%S")

    def get_file_extension(self, data):
        if data.startswith("<?xml") and data.find("<svg") > -1:
            return ".svg"
        elif data.startswith("<?xml"):
            return ".xml"
        else:
            return ".txt"

    def write_llm_prompt(self, id, prompt):
        """Write data given to the LLM to a file."""

        filename = "cmi-" + self.get_timestamp() + "-" + str(id) + "-llm-prompt.txt"

        with open(os.path.join(self.directory, filename), 'w') as f:
            f.write(prompt)

    def write_llm_response(self, id, response):
        """Write data returned by the LLM to a file."""

        filename = "cmi-" + self.get_timestamp() + "-" + str(id) + "-llm-response.txt"

        with open(os.path.join(self.directory, filename), 'w') as f:
            f.write(response)

    def write_interpreter_input(self, id, input):
        """Write data given to the interpreter to a file."""

        filename = "cmi-" + self.get_timestamp() + "-" + str(id) + "-int-input" + self.get_file_extension(input)

        with open(os.path.join(self.directory, filename), 'w') as f:
            f.write(input)

    def write_interpreter_output(self, id, output):
        """Write data returned by the interpreter to a file."""

        filename = "cmi-" + self.get_timestamp() + "-" + str(id) + "-int-output" + self.get_file_extension(output)

        with open(os.path.join(self.directory, filename), 'w') as f:
            f.write(output)

    def create_conversation(self, init_message):
        """Create a new JSON file with current timestamp for storing a new conversation."""
        
        self.init_message = init_message

        self.message_id = 0
        self.last_llm = ""
        self.last_llm_config = ""
        self.last_int = ""
        self.last_int_config = ""

        self.conversation_id = "cmi-" + self.get_timestamp()

        self.directory = os.path.join(DIRECTORY, self.conversation_id)
        self.log_file = os.path.join(DIRECTORY, self.conversation_id, self.conversation_id + ".json")

    def set_llm_configuration(self, selected_llm, llm_config):
        """Store the selected LLM with configuration parameters"""

        if self.last_llm != str(selected_llm) or self.last_llm_config != str(llm_config):
            self.last_llm = str(selected_llm)
            self.last_llm_config = str(llm_config)
            next_message_id = self.message_id + 1

            c = {
                TIMESTAMP: int(time.time()),
                MESSAGE_ID: next_message_id,
                LLM: selected_llm,
                LLM_CONFIG: llm_config
            }

            self.write_log_file(LLM_CONFIG_LIST, c)

    def set_interpreter_configuration(self, selected_int, int_config):
        """Store the selected interpreter with configuration parameters"""

        if self.last_int != str(selected_int) or self.last_int_config != str(int_config):
            self.last_int = str(selected_int)
            self.last_int_config = str(int_config)
            next_message_id = self.message_id + 1

            c = {
                TIMESTAMP: int(time.time()),
                MESSAGE_ID: next_message_id,
                INT: selected_int,
                INT_CONFIG: int_config
            }

            self.write_log_file(INT_CONFIG_LIST, c)

    def insert_init_message(self):

        c = {
            TIMESTAMP: int(time.time()),
            MESSAGE_ID: self.message_id, 
            INIT_MESSAGE: self.init_message
        }

        self.write_log_file(CONVERSATION, c)

    def insert_prompt(self, prompt):
        """Store a user-provided prompt as part of the current conversaion"""

        if self.message_id == 0:
            self.insert_init_message()

        self.message_id += 1
        
        c = {
            TIMESTAMP: int(time.time()),
            MESSAGE_ID: self.message_id, 
            PROMPT: prompt
        }

        self.write_log_file(CONVERSATION, c)
        self.write_llm_prompt(self.message_id, prompt)

    def insert_llm_response(self, response, execution_duration_ns):
        """Store a LLM response as part of the current conversaion"""

        self.message_id += 1

        c = {
            TIMESTAMP: int(time.time()),
            MESSAGE_ID: self.message_id,
            EXEC_DURATION_S: execution_duration_ns/1e+9,
            RESPONSE: response.strip()
        }

        self.write_log_file(CONVERSATION, c)
        self.write_llm_response(self.message_id, response)

    def insert_interpreter_input(self, input):
        """Store an interpreter input as part of the current conversaion"""

        self.message_id += 1
        c = {
            TIMESTAMP: int(time.time()),
            MESSAGE_ID: self.message_id, 
            INT_INPUT: input
        }

        self.write_log_file(CONVERSATION, c)
        self.write_interpreter_input(self.message_id, input)

    def insert_interpreter_output(self, output, execution_duration_ns):
        """Store an interpreter output as part of the current conversaion"""

        self.message_id += 1
        c = {
            TIMESTAMP: int(time.time()),
            MESSAGE_ID: self.message_id, 
            EXEC_DURATION_S: execution_duration_ns/1e+10,
            INT_OUTPUT: output
        }

        self.write_log_file(CONVERSATION, c)
        self.write_interpreter_output(self.message_id, output)

    def insert_message(self, message):
        """Stores an arbitrary message"""

        self.message_id += 1
        c = {
            TIMESTAMP: int(time.time()),
            MESSAGE_ID: self.message_id, 
            MESSAGE: message
        }

        self.write_log_file(CONVERSATION, c)
