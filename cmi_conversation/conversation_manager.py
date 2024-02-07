import sys
import os
import re
from time import perf_counter_ns

import cmi_llm_local.llm_api_client as llm_api_client
import cmi_llm_local.llm_runtime as llm_runtime
import cmi_interpreter.interpreter_runtime as interpreter_runtime

API_ID_LIST = llm_api_client.LLM_API_IDS + interpreter_runtime.INT_API_IDS
INT_API_ID_LIST = interpreter_runtime.INT_API_IDS
LLM_API_ID_LIST = llm_api_client.LLM_API_IDS
LLM_RUNTIME_ID_LIST = llm_runtime.LLM_RUNTIME_IDS
LLM_BY_ID = llm_api_client.LLM_BY_ID | llm_runtime.LLM_BY_ID

INT_ID_LIST = interpreter_runtime.INT_IDS

class ConversationManager:
    """Manages the selected LLM and interpreter with parameters"""

    def __init__(self, api_keys, api_endpoints, llm_api_client, llm_runtime, interpreter_runtime, data_store):
        print("Load Conversation Manager ...")
        self.api_keys = api_keys
        self.api_endpoints = api_endpoints
        self.llm_api_client = llm_api_client
        self.llm_runtime = llm_runtime
        self.interpreter_runtime = interpreter_runtime
        self.data_store = data_store
        self.conversational_ui = None
        self.selected_llm_id = None
        self.selected_int_id = None
        self.llm_parameters = None
        self.llm_parameters_default = None
        self.int_parameters = None
        self.int_parameters_default = None

    def set_conversational_ui(self, conversational_ui):
        self.conversational_ui = conversational_ui

    def select_llm(self, selected_llm_id):
        """
        If the given LLM was not selected before, it is set selected, LLM parameters are reset, and 
        True is returned; otherwise False is returned.
        """

        if not self.selected_llm_id or self.selected_llm_id != selected_llm_id:
            print("Selected LLM:", selected_llm_id)
            self.selected_llm_id = selected_llm_id
            self.selected_llm_api_id = LLM_BY_ID[selected_llm_id]
            print("Reset LLM parameters")
            self.llm_parameters = None
            self.llm_parameters_default = None
            self.file_upload = None
            return True

        return False

    def set_llm_parameters(self):
        """
        Sets initial LLM parameters and initializes a LLM API or a local runtime. 
        Returns parameters as parameter binding to be connected to, e.g., UI controls.
        """

        if not self.llm_parameters:

            # set default values for the selected LLM, running via API or a runtime
            for api_id in LLM_API_ID_LIST:
                if self.selected_llm_id.startswith(api_id):
                    self.llm_parameters_default = llm_api_client.PARAMETER_DEFAULTS[api_id].copy()
                    self.llm_parameters = llm_api_client.PARAMETER_DEFAULTS[api_id].copy()
                    break

            for rt_id in LLM_RUNTIME_ID_LIST:
                if self.selected_llm_id.startswith(rt_id):
                    self.llm_parameters_default = llm_runtime.PARAMETER_DEFAULTS[rt_id].copy()
                    self.llm_parameters = llm_runtime.PARAMETER_DEFAULTS[rt_id].copy()
                    break

            # get API parameters
            api_key = ""
            api_endpoint = ""
            api_selected = False
            for api_id in LLM_API_ID_LIST:
                if self.selected_llm_id.startswith(api_id):
                    api_selected = True
                    if api_id in self.api_keys.keys():
                        api_key = self.api_keys[api_id]
                    if api_id in self.api_endpoints.keys():
                        api_endpoint = self.api_endpoints[api_id]
                    break

            # initialize LLM API or runtime
            if api_selected:
                self.llm_api_client.initialize_llm(
                    self.selected_llm_id, self.selected_llm_api_id, self.llm_parameters, api_key, api_endpoint)
                self.data_store.create_conversation()
            else:
                self.llm_runtime.load_llm_files(
                    self.selected_llm_id, self.llm_parameters)
                self.data_store.create_conversation()
            
        return self.llm_parameters

    def select_interpreter(self, selected_int_id):
        """
        If the given interpreter was not selected before, it is set selected, interpreter parameters are reset, and 
        True is returned; otherwise False is returned.
        """

        if not self.selected_int_id or self.selected_int_id != selected_int_id:
            print("Selected interpreter:", selected_int_id)
            self.selected_int_id = selected_int_id
            print("Reset interpreter parameters")
            self.int_parameters = None
            self.int_parameters_default = None
            return True

        return False

    def set_interpreter_parameters(self):
        """
        Sets initial interpreter parameters and initializes an interpreter. 
        Returns parameters as parameter binding to be connected to, e.g., UI controls.
        """

        if not self.int_parameters:
            # set default values depending on the interpreter
            for int_id in INT_ID_LIST:
                if self.selected_int_id.startswith(int_id):
                    self.int_parameters = interpreter_runtime.PARAMETER_DEFAULTS[int_id].copy()
                    self.int_parameters_default = interpreter_runtime.PARAMETER_DEFAULTS[int_id].copy()
                    break

            # get API parameters
            api_key = ""
            api_endpoint = ""
            api_selected = False
            for api_id in INT_API_ID_LIST:
                if self.selected_int_id.startswith(api_id):
                    api_selected = True
                    if api_id in self.api_keys.keys():
                        api_key = self.api_keys[api_id]
                    if api_id in self.api_endpoints.keys():
                        api_endpoint = self.api_endpoints[api_id]
                    break

            self.interpreter_runtime.initialize_interpreter(self.selected_int_id, self.int_parameters, api_key, api_endpoint)

        return self.int_parameters

    def enter_prompt(self, context, prompt):
        """
        Executes a prompt string with the given context as message array.
        Returns the response as tuple (items_wrapped, item_function) where item_function is a 
        lambda function extracting the wrapped response items.
        """
        print("Prompt:", prompt)

        # store LLM configuration and prompt
        self.data_store.set_llm_configuration(self.selected_llm_id, self.llm_parameters)
        self.data_store.set_interpreter_configuration(self.selected_int_id, self.int_parameters)
        self.data_store.insert_prompt(prompt)
        
        # run prompt with an API
        for api_id in LLM_API_ID_LIST:
            if self.selected_llm_id.startswith(api_id):

                print("LLM parameters:", self.llm_parameters)
                print("Interpreter parameters:", self.int_parameters)
                t_start = perf_counter_ns()
                (items_wrapped, item_function) = self.llm_api_client.request_run_prompt(context, prompt)
                break

        # run prompt with a runtime
        for rt_id in LLM_RUNTIME_ID_LIST:
            if self.selected_llm_id.startswith(rt_id):

                print("LLM parameters:", self.llm_parameters)
                print("Interpreter parameters:", self.int_parameters)
                (items_wrapped, item_function) = self.llm_runtime.run_prompt(context)
                break
        
        return (items_wrapped, item_function, t_start)

    def process_llm_response(self, llm_response, execution_duration):
        """
        Parses an LLM response. If an LLM response contains concrete syntax, it is parsed and returned, otherwise None. 
        """
        
        output = None

        self.data_store.insert_llm_response(llm_response, execution_duration)
        int_syntax_match_code = re.search(interpreter_runtime.SYNTAX_MATCH[self.selected_int_id], llm_response, flags=re.DOTALL)
        # try to find conrete syntax
        if int_syntax_match_code:
            output = int_syntax_match_code.group(1)
        else:
            # try to find any syntax in a code block
            int_syntax_match_code = re.search(interpreter_runtime.SYNTAX_MATCH_CODE_BLOCK[self.selected_int_id], llm_response, flags=re.DOTALL)
            if int_syntax_match_code:
                output = int_syntax_match_code.group(1)
            #else:
            # try to find any code word
            #int_syntax_match_code = re.search(interpreter_runtime.SYNTAX_MATCH_CODE_WORD, llm_response, flags=re.DOTALL)
            #if int_syntax_match_code:
            #    output = int_syntax_match_code.group(1)
        
        return output

    def execute_interpreter(self, input_syntax):
        """
        Starts the interpreter and returns the result and execution time.
        """
        
        #bpmn_test_file = "test.bpmn"
        #bpmn_syntax_test = ""
        #if os.path.isfile(bpmn_test_file):
        #    with open(bpmn_test_file, "r") as file:
        #        bpmn_syntax_test = file.read()
        #        print("Loaded BPMN test syntax")
        #        llm_response += "\n" + bpmn_syntax_test

        output = None

        self.data_store.set_interpreter_configuration(self.selected_int_id, self.int_parameters)
        self.data_store.insert_interpreter_input(input_syntax)
        t_start = perf_counter_ns()
        interpreter_output = self.interpreter_runtime.run_syntax(input_syntax)
        t_stop = perf_counter_ns()
        execution_duration = (t_stop-t_start)
        print("Interpreter total execution duration [ns]:", execution_duration)
        if interpreter_output:
            #self.conversational_ui.append_interpreter_output(image_output=interpreter_output)
            output = interpreter_output
            self.data_store.insert_interpreter_output(output, execution_duration)
        
        return output

    def clear_chat_history(self):
        self.llm_api_client.clear_returned_context()
        self.llm_runtime.clear_returned_context()

    def remove_last_message(self):
        self.llm_api_client.clear_returned_context()
        self.llm_runtime.clear_returned_context()
