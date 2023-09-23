import sys
import getopt
import streamlit as st
import os
from unittest import result
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
    print("Usage: cmi.py [-h|--help] [-a|--api-key <api_id>:<api_key>]* [-p|--port <ui_port>]")
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
    """Parses and stores API keys"""

    global api_keys

    api_id_key = key_spec.split(":")
    if len(api_id_key) == 2:
        api_id = api_id_key[0]
        api_key = api_id_key[1]
        print("Setting API-Key:", api_id)
        api_keys[api_id] = api_key

def set_webui_port(port_spec):
    """Parses and sets the port where the web-based UI will be available"""

    global ui_port

    port_nr = None
    if isinstance(port_spec, str):
        port_nr = int(port_spec)
    elif isinstance(port_spec, int):
        port_nr = port_spec

    if port_nr and port_nr >= 1024 and port_nr <= 65535:
        print("Setting Web-UI port:", port_nr)
        ui_port = port_nr
    else:
        print("Web-UI port format error:", port_nr)
        sys.exit(1)

def activate_streamlit():
    """Activates the Streamlit web UI if it has not been activated before"""

    # ensure streamlit is started from the main module only and only if not active
    if __name__ == '__main__' and not streamlit_activated:
        print("Activating Streamlit ...")
        user_argv = sys.argv[1:].copy()
        sys.argv = ["streamlit", "run", __file__, "--server.port", str(ui_port), "--", "--streamlit-startup"] + user_argv
        sys.exit(stweb.main())


class CMI:
    """Conceptual Model Interpreter (CMI)"""

    def __init__(self):
        self.llm_api_client = None
        self.llm_runtime = None
        self.interpreter_runtime = None
        self.data_store = None
        self.conversation_manager = None
        self.conversational_ui = None


    def load_components(self):
        """Load components after the initial startup"""

        cmi_init_message = ""

        cmi_init_message += "API keys found: "
        cmi_init_message += ", ".join(api_keys.keys())

        if not self.conversational_ui:

            # LLM Local
            self.llm_api_client = llm_api_client.LLMApiClient()
            self.llm_runtime = llm_runtime.LLMRuntime()

            # Interpreter
            self.interpreter_runtime = interpreter_runtime.InterpreterRuntime()
            
            # Data Store
            self.data_store = data_store.DataStore()

            # Conversation
            self.conversation_manager = conversation_manager.ConversationManager(api_keys, self.llm_api_client, self.llm_runtime, self.interpreter_runtime, self.data_store)

            ui_title = "LLM Conceptual Model Interpreter"
            self.conversational_ui = conversational_ui.ConversationalUI(ui_port, ui_title, cmi_init_message, api_keys, self.conversation_manager)

            self.conversation_manager.set_conversational_ui(self.conversational_ui)

    

def parse_cli():
    """Parse command line interface options and arguments"""

    try:
        opts, args = getopt.getopt(sys.argv[1:], "a:p:h",
            ["help", "api-key=", "port=", "streamlit-startup"])

    except getopt.GetoptError as err:
        print(err)
        print_usage()

    global streamlit_activated
        
    for opt, arg in opts:
        if opt in ("-a", "--api-key"):
            set_api_key(arg.strip())
        elif opt in ("-p", "--port"):
            set_webui_port(arg.strip())
        elif opt in ("-h", "--help"):
            print_usage()
            sys.exit()
        elif opt in ("--streamlit-startup"):
            streamlit_activated = True
        else:
            print(CMI_TITLE, CMI_VERSION)


if SESSION_KEY_CMI in st.session_state:
    # ongoing session
    cmi = st.session_state[SESSION_KEY_CMI]
else:
    # initial startup
    parse_cli()
    if not streamlit_activated:
        activate_streamlit()
    cmi = CMI()
    st.session_state[SESSION_KEY_CMI] = cmi
    cmi.load_components()

# update the web UI
cmi.conversational_ui.update_web_ui()
