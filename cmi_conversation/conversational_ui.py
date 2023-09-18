import sys
import requests

import streamlit as st
from streamlit.web import cli as stweb

import cmi_conversation.conversation_manager as conversation_manager

SESSION_KEY_MESSAGES = "messages/"

SESSION_KEY_LLM_UI_INPUT = "ui/input/llm/"
SESSION_KEY_INT_UI_INPUT = "ui/input/int/"

ROLE = "role"
ROLE_AS = "assistant"
ROLE_US = "user"
ROLE_IN = "interpreter"

MSG = "message"
MSG_FORMAT = "format"
MSG_FORMAT_TXT = "text"
MSG_FORMAT_IMG = "image"

INIT_MSG = "How may I assist you today?"

AVATAR = "avatar"
AVATAR_ASSIST = "A"
AVATAR_USER = "U"
AVATAR_INTER = "I"

class ConversationalUI:

    def __init__(self, ui_port, ui_title, ui_init_message, api_keys, conversation_manager):
        print("Load Conversational UI ...")
        self.ui_port = ui_port
        self.ui_title = ui_title
        self.ui_init_message = ui_init_message
        self.api_keys = api_keys
        self.conversation_manager = conversation_manager

    def update_web_ui(self):

        # App title
        st.set_page_config(page_title=self.ui_title)
        
        # Initialize session storage for messages
        if SESSION_KEY_MESSAGES not in st.session_state.keys():
            st.session_state[SESSION_KEY_MESSAGES] = [ {ROLE: ROLE_AS, MSG: INIT_MSG, MSG_FORMAT: MSG_FORMAT_TXT} ]

        # Sidebar
        with st.sidebar:
            st.title(self.ui_title)

            st.subheader('LLM Settings')

            selected_llm = st.sidebar.selectbox(
                'Model', 
                conversation_manager.LLM_BY_ID.keys(), 
                key='selected_llm')
            
            new_llm_selected = self.conversation_manager.select_llm(selected_llm)

            st.info(self.ui_init_message)


            #st.subheader('LLM Parameters')

            llm_param_binding = self.conversation_manager.set_llm_parameters()
            
            for p in llm_param_binding.keys():
                if new_llm_selected:
                    st.session_state[SESSION_KEY_LLM_UI_INPUT + p] = self.conversation_manager.llm_parameters_default[p]
                if p == 'temperature':
                    llm_param_binding[p] = st.sidebar.slider(p, min_value=0.01, max_value=5.0, step=0.01, key=SESSION_KEY_LLM_UI_INPUT + p)
                elif p == 'top_p':
                    llm_param_binding[p] = st.sidebar.slider(p, min_value=0.01, max_value=1.0, step=0.01, key=SESSION_KEY_LLM_UI_INPUT + p)
                elif p == 'top_k':
                    llm_param_binding[p] = st.sidebar.number_input(p, min_value=1, step=1, key=SESSION_KEY_LLM_UI_INPUT + p)
                elif p == 'max_new_tokens' or p == 'n_tokens_max':
                    llm_param_binding[p] = st.sidebar.number_input(p, min_value=64, step=8, key=SESSION_KEY_LLM_UI_INPUT + p)
                elif p == 'min_new_tokens':
                    llm_param_binding[p] = st.sidebar.number_input(p, min_value=-1, step=1, key=SESSION_KEY_LLM_UI_INPUT + p)
                elif p == 'frequency_penalty':
                    llm_param_binding[p] = st.sidebar.slider(p, min_value=-2.0, max_value=2.0, step=0.01, key=SESSION_KEY_LLM_UI_INPUT + p)
                elif p == 'presence_penalty':
                    llm_param_binding[p] = st.sidebar.slider(p, min_value=-2.0, max_value=2.0, step=0.01, key=SESSION_KEY_LLM_UI_INPUT + p)
                #elif p == 'stop_sequences':
                #    stop_sequences = st.sidebar.text_input('stop_sequences', value=parameters["stop_sequences"])
                #elif p == 'debug':
                #    st.sidebar.text('debug')
                #    debug = st.sidebar.toggle('debug_enabled') #, label_visibility='hidden')
                else:
                    if isinstance(llm_param_binding[p], int):
                        llm_param_binding[p] = st.sidebar.number_input(p, step=1, key=SESSION_KEY_LLM_UI_INPUT + p)
                    elif isinstance(llm_param_binding[p], str):
                        llm_param_binding[p] = st.sidebar.text_input(p, key=SESSION_KEY_LLM_UI_INPUT + p)
                    else:
                        llm_param_binding[p] = st.sidebar.number_input(p, key=SESSION_KEY_LLM_UI_INPUT + p)


            st.subheader('Interpreter Settings')

            selected_interpreter = st.sidebar.selectbox(
                'Interpreter',
                conversation_manager.INTERPRETER_ID_LIST,
                key='selected_interpreter')

            new_interpreter_selected = self.conversation_manager.select_interpreter(selected_interpreter)

            int_param_binding = self.conversation_manager.set_interpreter_parameters()

            #st.subheader('Interpreter Parameters')
                
            for p in int_param_binding.keys():
                if p == 'Output format':
                    list = self.conversation_manager.int_parameters_default[p].copy()
                    int_param_binding[p] = st.sidebar.selectbox(p, list, key=SESSION_KEY_INT_UI_INPUT + p)
                elif p == 'Use cache':
                    int_param_binding[p] = st.sidebar.toggle(p, key=SESSION_KEY_INT_UI_INPUT + p)
                else:
                    if new_interpreter_selected:
                        st.session_state[SESSION_KEY_INT_UI_INPUT + p] = self.conversation_manager.int_parameters_default[p]
                    if isinstance(int_param_binding[p], int):
                        int_param_binding[p] = st.sidebar.number_input(p, step=1, key=SESSION_KEY_INT_UI_INPUT + p)
                    elif isinstance(llm_param_binding[p], str):
                        int_param_binding[p] = st.sidebar.text_input(p, key=SESSION_KEY_INT_UI_INPUT + p)
                    else:
                        int_param_binding[p] = st.sidebar.number_input(p, key=SESSION_KEY_INT_UI_INPUT + p)

            def clear_chat_history():
                st.session_state[SESSION_KEY_MESSAGES] = [ {ROLE: ROLE_AS, MSG: INIT_MSG, MSG_FORMAT: MSG_FORMAT_TXT} ]

            st.sidebar.button('Reset Conversaion', on_click=clear_chat_history)

        for message in st.session_state[SESSION_KEY_MESSAGES]:
            avatar = None
            if message[ROLE] == ROLE_IN:
                avatar = AVATAR_INTER
            with st.chat_message(message[ROLE]):
                if MSG_FORMAT in message.keys():
                    if message[MSG_FORMAT] == MSG_FORMAT_TXT:
                        st.write(message[MSG])
                    if message[MSG_FORMAT] == MSG_FORMAT_IMG:
                        st.image(message[MSG])
                else:
                    print("Unknown format: " + str(message.keys()))
                    st.write(message[MSG])

        def append_llm_response(text_response):
            message = {ROLE: ROLE_AS, MSG: text_response, MSG_FORMAT: MSG_FORMAT_TXT}
            st.session_state[SESSION_KEY_MESSAGES].append(message)

        def append_interpreter_output(text_output=None, image_output=None):
            if text_output:
                message = {ROLE: ROLE_IN, MSG: text_output, MSG_FORMAT: MSG_FORMAT_TXT}
                st.session_state[SESSION_KEY_MESSAGES].append(message)
            if image_output:
                message = {ROLE: ROLE_IN, MSG: image_output, MSG_FORMAT: MSG_FORMAT_IMG}
                st.session_state[SESSION_KEY_MESSAGES].append(message)

        def append_user_prompt(prompt):
            st.session_state[SESSION_KEY_MESSAGES].append({ROLE: ROLE_US, MSG: prompt, MSG_FORMAT: MSG_FORMAT_TXT})
            with st.chat_message(ROLE_US):
                st.write(prompt)

        def run_llm(prompt):
            llm_response = ''

            context = st.session_state[SESSION_KEY_MESSAGES]

            with st.chat_message(ROLE_AS):
                with st.spinner(f"Running Inference: {selected_llm} ..."):
                    items_wrapped = []
                    item_function = lambda item: item
                    try:
                        (items_wrapped, item_function) = self.conversation_manager.enter_prompt(context, prompt)
                        placeholder = st.empty()
                        for item in items_wrapped:
                            llm_response += item_function(item)
                            placeholder.markdown(llm_response + "▌")
                        placeholder.markdown(llm_response)
                    except requests.exceptions.ChunkedEncodingError as e:
                        placeholder.markdown(e)

            append_llm_response(llm_response)

            return llm_response

        def run_interpreter(response):
            input_syntax = self.conversation_manager.parse_llm_response(response)

            if input_syntax:
                with st.chat_message(ROLE_IN):
                    placeholder = st.empty()
                    interpreter_output = None
                    with st.spinner(f"Running interpreter: {self.conversation_manager.selected_int_id} ..."):
                        try:
                            interpreter_output = self.conversation_manager.parse_llm_response(response, input_syntax=input_syntax)
                        except requests.exceptions.HTTPError as e:
                            placeholder.error(f"HTTP Error {e}", icon='⚠️')
                    if interpreter_output:
                        placeholder.text(self.conversation_manager.selected_int_id)
                        placeholder.image(interpreter_output)
                        append_interpreter_output(image_output=interpreter_output)


        prompt = st.chat_input() #st.chat_input(disabled=(len(api_key) < 1))

        if prompt:
            append_user_prompt(prompt)

            # if last message is a user message
            if st.session_state[SESSION_KEY_MESSAGES][-1][ROLE] == ROLE_US:

                # run interpreter on prompt
                #run_interpreter(prompt)

                # run llm
                llm_response = run_llm(prompt)

                # run interpreter on response
                run_interpreter(llm_response)


    #def setup_api_keys(self):
        #try:
        #    if KEY_SEC_REPLICATE in st.secrets:
        #        api_key_replicate = st.secrets[KEY_SEC_REPLICATE]
        #    else:
        #        api_key_replicate = st.text_input('Enter API token:', type='password')
        #except FileNotFoundError as e:
        #    if len(api_key_replicate) == 0:
        #        api_key_replicate = st.text_input('Enter API token:', type='password')
        #        st.markdown(f"Note: No secrets file has been found {e}")
        #if not (api_key_replicate.startswith('r8_') and len(api_key_replicate)==40):
        #    st.warning('Please enter your credentials!', icon='⚠️')
