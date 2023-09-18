import sys
import os
import re

import cmi_llm_local.llm_api_client as llm_api_client
import cmi_llm_local.llm_runtime as llm_runtime
import cmi_interpreter.interpreter_runtime as interpreter_runtime

LLM_API_ID_LIST = llm_api_client.LLM_API_IDS
LLM_RUNTIME_ID_LIST = llm_runtime.LLM_RUNTIME_IDS
LLM_BY_ID = llm_api_client.LLM_BY_ID | llm_runtime.LLM_BY_ID

INTERPRETER_ID_LIST = interpreter_runtime.INTERPRETER_IDS

class ConversationManager:

    def __init__(self, api_keys, llm_api_client, llm_runtime, interpreter_runtime, data_store):
        print("Load Conversation Manager ...")
        self.api_keys = api_keys
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

        if not self.selected_llm_id or self.selected_llm_id != selected_llm_id:
            print("Selected LLM:", selected_llm_id)
            self.selected_llm_id = selected_llm_id
            self.selected_llm_api_id = LLM_BY_ID[selected_llm_id]
            print("Reset LLM parameters")
            self.llm_parameters = None
            self.llm_parameters_default = None
            return True

        return False

    def set_llm_parameters(self):

        if not self.llm_parameters:

            # set default values depending on the API or runtime
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

            api_key = ""
            api_selected = False
            for api_id in LLM_API_ID_LIST:
                if self.selected_llm_id.startswith(api_id):
                    api_selected = True
                    if api_id in self.api_keys.keys():
                        api_key = self.api_keys[api_id]
                    break

            if api_selected:
                self.llm_api_client.initialize_llm(
                    self.selected_llm_id, self.selected_llm_api_id, self.llm_parameters, api_key)
                self.data_store.create_conversation()
                self.data_store.set_llm_configuration(self.selected_llm_id, self.llm_parameters)
            else:
                self.llm_runtime.load_llm_files(
                    self.selected_llm_id, self.llm_parameters)
                self.data_store.create_conversation()
                self.data_store.set_llm_configuration(self.selected_llm_id, self.llm_parameters)
            
        return self.llm_parameters

    def select_interpreter(self, selected_int_id):

        if not self.selected_int_id or self.selected_int_id != selected_int_id:
            print("Selected interpreter:", selected_int_id)
            self.selected_int_id = selected_int_id
            print("Reset interpreter parameters")
            self.int_parameters = None
            self.int_parameters_default = None
            return True

        return False

    def set_interpreter_parameters(self):

        if not self.int_parameters:
            # set default values depending on the interpreter
            for int_id in INTERPRETER_ID_LIST:
                if self.selected_int_id.startswith(int_id):
                    self.int_parameters = interpreter_runtime.PARAMETER_DEFAULTS[int_id].copy()
                    self.int_parameters_default = interpreter_runtime.PARAMETER_DEFAULTS[int_id].copy()
                    break
        
            self.interpreter_runtime.initialize_interpreter(self.selected_int_id, self.int_parameters)

            self.data_store.set_interpreter_configuration(self.selected_int_id, self.int_parameters)

        return self.int_parameters

    def enter_prompt(self, context, prompt):
        print("Prompt:", prompt)

        self.data_store.set_llm_configuration(self.selected_llm_id, self.llm_parameters)
        self.data_store.insert_prompt(prompt)
        
        for api_id in LLM_API_ID_LIST:
            if self.selected_llm_id.startswith(api_id):

                print("LLM parameters:", self.llm_parameters)
                print("Interpreter parameters:", self.int_parameters)
                (items_wrapped, item_function) = self.llm_api_client.request_run_prompt(context)
                break

        for rt_id in LLM_RUNTIME_ID_LIST:
            if self.selected_llm_id.startswith(rt_id):

                print("LLM parameters:", self.llm_parameters)
                print("Interpreter parameters:", self.int_parameters)
                (items_wrapped, item_function) = self.llm_runtime.run_prompt(context)
                break
        
        return (items_wrapped, item_function)

    def parse_llm_response(self, llm_response, input_syntax=None):

        output = None

        if not input_syntax:
            self.data_store.insert_llm_response(llm_response)
            int_syntax_match_code = re.search(interpreter_runtime.SYNTAX_MATCH[self.selected_int_id], llm_response, flags=re.DOTALL)
            if int_syntax_match_code:
                output = int_syntax_match_code.group(1)
            #else:
                # try to find any code block
                #int_syntax_match_code = re.search(interpreter_runtime.SYNTAX_MATCH_CODE_BLOCK, llm_response, flags=re.DOTALL)
                #if int_syntax_match_code:
                #    output = int_syntax_match_code.group(1)
            
        else:
            interpreter_output = self.interpreter_runtime.run_syntax(input_syntax)
            if interpreter_output:
                #self.conversational_ui.append_interpreter_output(image_output=interpreter_output)
                output = interpreter_output
                self.data_store.set_interpreter_configuration(self.selected_int_id, self.int_parameters)
                self.data_store.insert_interpreter_output(output)
        
        return output
            
