from encodings import normalize_encoding
from os import stat
import getopt
import uuid
from unittest import result

import sys
import streamlit as st
from streamlit.web import cli as stweb

import cmi_conversation.conversational_ui as conversational_ui
import cmi_conversation.conversation_manager as conversation_manager
import cmi_data_store.data_store as data_store
import cmi_llm_local.llm_api_client as llm_api_client
import cmi_llm_local.llm_runtime as llm_runtime
import cmi_interpreter.interpreter_runtime as interpreter_runtime

CMI_TITLE = "CMI Test Environment"
CMI_VERSION = "v0.1"
SESSION_KEY_CMI = "CMI"

streamlit_activated = False
api_keys = {}
ui_port = 8501

def print_usage():
    print(CMI_TITLE, CMI_VERSION)
    print("")
    print("Usage: cmi.py [-h|--help] [-a|--api-key <api_id>:<api_key>]* [-p <ui_port>]")
    print("")

    api_id_options = " | ".join(conversation_manager.LLM_API_ID_LIST)
    print("<api_id> =", api_id_options)
    print("")
    
    print("Supported local LLM runtime:")
    for rt_id in conversation_manager.LLM_RUNTIME_ID_LIST:
        print("-", rt_id)
    print("")

    print("Supported LLM API clients:")
    for api_id in conversation_manager.LLM_API_ID_LIST:
        print("-", api_id)
    print("")

    print("Supported LLMs:")
    for llm_id in conversation_manager.LLM_BY_ID.keys():
        print("-", llm_id)
    print("")
    
    print("Supported Interpreters:")
    for llm_id in conversation_manager.INTERPRETER_ID_LIST:
        print("-", llm_id)
    print("")

    print("The web-based UI will be started at port <ui_port>, default:", ui_port)
    print("")
    sys.exit()

def set_api_key(key_spec):
    api_id_key = key_spec.split(":")
    if len(api_id_key) == 2:
        api_id = api_id_key[0]
        api_key = api_id_key[1]
        print("Setting API-Key:", api_id)
        api_keys[api_id] = api_key

def activate_streamlit():

    # ensure streamlit is started form the main module only and only if not active
    if __name__ == '__main__' and not streamlit_activated:
        print("Activating Streamlit ...")
        user_argv = sys.argv[1:].copy()
        sys.argv = ["streamlit", "run", __file__, "--", "--streamlit-startup"] + user_argv
        sys.exit(stweb.main())

class CMI:

    def __init__(self):
        self.llm_api_cl = None
        self.rt = None
        self.interpreter_rt = None
        self.data_st = None
        self.conv_ma = None
        self.conv_ui = None


    def initialize_components(self):

        cmi_init_message = ""

        cmi_init_message += "API keys found: "
        cmi_init_message += ", ".join(api_keys.keys())

        if not self.conv_ui:

            # LLM Local
            self.llm_api_cl = llm_api_client.LLMApiClient()
            self.llm_rt = llm_runtime.LLMRuntime()

            # Interpreter
            self.interpreter_rt = interpreter_runtime.InterpreterRuntime()
            
            # Data Store
            self.data_st = data_store.DataStore()

            # Conversation
            self.conv_ma = conversation_manager.ConversationManager(api_keys, self.llm_api_cl, self.llm_rt, self.interpreter_rt, self.data_st)

            ui_title = "LLM Conceptual Model Interpreter"
            self.conv_ui = conversational_ui.ConversationalUI(ui_port, ui_title, cmi_init_message, api_keys, self.conv_ma)

            self.conv_ma.set_conversational_ui(self.conv_ui)

    

def parse_cli():

    try:
        opts, args = getopt.getopt(sys.argv[1:], "a:h",
            ["help", "api-key=", "streamlit-startup"])

    except getopt.GetoptError as err:
        print(err)
        print_usage()

    global streamlit_activated
        
    for opt, arg in opts:
        if opt in ("-a", "--api-key"):
            set_api_key(arg.strip())
        elif opt in ("-h", "--help"):
            print_usage()
            sys.exit()
        elif opt in ("--streamlit-startup"):
            streamlit_activated = True
        else:
            print(CMI_TITLE, CMI_VERSION)



if SESSION_KEY_CMI in st.session_state:
    cmi = st.session_state[SESSION_KEY_CMI]
else:
    parse_cli()
    if not streamlit_activated:
        activate_streamlit()
    cmi = CMI()
    st.session_state[SESSION_KEY_CMI] = cmi
    cmi.initialize_components()

cmi.conv_ui.update_web_ui()
