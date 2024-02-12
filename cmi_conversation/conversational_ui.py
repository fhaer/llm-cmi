import sys
import requests
import time
import uuid
from time import perf_counter_ns
from io import StringIO

import streamlit as st
from streamlit.web import cli as stweb

import cmi_conversation.conversation_manager as conversation_manager

SESSION_KEY_MESSAGES = "messages/"
SESSION_KEY_CONTEXT_IDS = "context_ids/"

SESSION_KEY_LLM_UI_INPUT = "ui/input/llm/"
SESSION_KEY_INT_UI_INPUT = "ui/input/int/"

SESSION_KEY_PROMPT = "prompt/message"
SESSION_KEY_PROMPT_PERPEND = "prompt/message/prepend"
SESSION_KEY_PROMPT_APPEND = "prompt/message/append"

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
    """Web UI of the conversational interface using Streamlit"""

    def __init__(self, ui_port, ui_title, ui_init_message, api_keys, conversation_manager):
        print("Load Conversational UI ...")
        self.ui_port = ui_port
        self.ui_title = ui_title
        self.ui_init_message = ui_init_message
        self.api_keys = api_keys
        self.conversation_manager = conversation_manager

    def set_available_models(self, models):
        self.available_models = models

    def trigger_update(self, message):
        st.toast(message)
        st.experimental_rerun()

    def update_web_ui(self):
        """Updates the web UI with selectable LLMs, interpreters, current parameters, and messages of the conversation"""

        # App title
        st.set_page_config(page_title=self.ui_title)
        
        # Initialize session storage for messages and prompts
        if SESSION_KEY_MESSAGES not in st.session_state.keys():
            st.session_state[SESSION_KEY_MESSAGES] = [ {ROLE: ROLE_AS, MSG: INIT_MSG, MSG_FORMAT: MSG_FORMAT_TXT} ]
        if SESSION_KEY_PROMPT not in st.session_state.keys():
            st.session_state[SESSION_KEY_PROMPT] = ""
        if SESSION_KEY_PROMPT_APPEND not in st.session_state.keys():
            st.session_state[SESSION_KEY_PROMPT_APPEND] = ""
        if SESSION_KEY_PROMPT_PERPEND not in st.session_state.keys():
            st.session_state[SESSION_KEY_PROMPT_PERPEND] = ""

        # Remove all messages
        def clear_chat_history():
            st.session_state[SESSION_KEY_MESSAGES] = [ {ROLE: ROLE_AS, MSG: INIT_MSG, MSG_FORMAT: MSG_FORMAT_TXT} ]
            self.conversation_manager.clear_chat_history(INIT_MSG)

        # Enables displaying the file uploader in the chat
        def remove_last_prompt_and_response():
            # remove response (from LLM, interpreter)
            while len(st.session_state[SESSION_KEY_MESSAGES]) > 0 and st.session_state[SESSION_KEY_MESSAGES][-1][ROLE] != ROLE_US:
                st.session_state[SESSION_KEY_MESSAGES] = st.session_state[SESSION_KEY_MESSAGES][0:-1]
                self.conversation_manager.remove_last_message()
            # remove last user message
            while len(st.session_state[SESSION_KEY_MESSAGES]) > 0 and st.session_state[SESSION_KEY_MESSAGES][-1][ROLE] == ROLE_US:
                    st.session_state[SESSION_KEY_MESSAGES] = st.session_state[SESSION_KEY_MESSAGES][0:-1]
                    self.conversation_manager.remove_last_message()
        
        # Prepend text to the next prompt submitted by the user
        def prepend_to_next_prompt(prepend_message):
            st.session_state[SESSION_KEY_PROMPT_PERPEND] = prepend_message
            st.toast("File contents will be prepended to the next prompt submission")

        # Append text to the next prompt submitted by the user
        def append_to_next_prompt(append_message):
            st.session_state[SESSION_KEY_PROMPT_APPEND] = append_message
            st.toast("File contents will be appended to the next prompt submission")
       
        # Append text to the next prompt submitted by the user
        def set_prompt(message):
            st.session_state[SESSION_KEY_PROMPT] = message
       
        # Enables displaying the file uploader
        def show_file_uploader():
            if not "file_uploader_visible" in st.session_state or not st.session_state["file_uploader_visible"]:
                st.session_state["show_file_uploader"] = True
                
        # Disables displaying the file uploader
        def hide_file_uploader():
            st.session_state["show_file_uploader"] = False

        # Execute prompt
        def run_llm(prompt):
            llm_response = ''
            execution_duration = 0

            context = st.session_state[SESSION_KEY_MESSAGES]

            with st.chat_message(ROLE_AS):
                # start inference and stream response
                with st.spinner(f"Running Inference: {selected_llm} ..."):
                    # get reponse items and un-wrap using the provided function
                    items_wrapped = []
                    item_function = lambda item: item
                    try:
                        (items_wrapped, item_function, t_start) = self.conversation_manager.enter_prompt(context, prompt)
                        placeholder = st.empty()
                        for item in items_wrapped:
                            llm_response += item_function(item)
                            placeholder.markdown(llm_response + "▌")
                        t_stop = perf_counter_ns()
                        execution_duration = (t_stop-t_start)
                        print("LLM total execution duration [ns]:", execution_duration)
                        placeholder.markdown(llm_response)
                    except requests.exceptions.ChunkedEncodingError as e:
                        placeholder.markdown(e)

            # append response to session state
            message = {ROLE: ROLE_AS, MSG: llm_response, MSG_FORMAT: MSG_FORMAT_TXT}
            st.session_state[SESSION_KEY_MESSAGES].append(message)

            return (llm_response, execution_duration)

        # Add interpreter output to session state
        def append_interpreter_output(text_output=None, image_output=None):
            if text_output:
                message = {ROLE: ROLE_IN, MSG: text_output, MSG_FORMAT: MSG_FORMAT_TXT}
                st.session_state[SESSION_KEY_MESSAGES].append(message)
            if image_output:
                #print(image_output)
                message = {ROLE: ROLE_IN, MSG: image_output, MSG_FORMAT: MSG_FORMAT_IMG}
                st.session_state[SESSION_KEY_MESSAGES].append(message)

        # Execute interpreter
        def run_interpreter(input_syntax):

            if input_syntax:
                with st.chat_message(ROLE_IN):
                    # start interpreter and add rendered response
                    placeholder = st.empty()
                    interpreter_output = None
                    with st.spinner(f"Running interpreter: {self.conversation_manager.selected_int_id} ..."):
                        try:
                            interpreter_output = self.conversation_manager.execute_interpreter(input_syntax)
                        except requests.exceptions.HTTPError as e:
                            placeholder.error(f"HTTP Error {e}", icon='⚠️')
                    if interpreter_output:
                        placeholder.text(self.conversation_manager.selected_int_id)
                        placeholder.image(interpreter_output)
                        append_interpreter_output(image_output=interpreter_output)
                    else:
                        #placeholder.error("*Interpreter response empty*")
                        placeholder.write("*Interpreter response invalid*")
                        append_interpreter_output(text_output="*Interpreter response invalid*")

        # Submit user-provided prompt
        def submit_user_prompt():

            prompt = ""

            # construct prompt
            if st.session_state[SESSION_KEY_PROMPT_PERPEND]:
                # Streamlit requires two whitespace characters in front of a newline character (markdown syntax)
                prompt = st.session_state[SESSION_KEY_PROMPT_PERPEND] + "  \n"

            prompt += st.session_state[SESSION_KEY_PROMPT]

            if st.session_state[SESSION_KEY_PROMPT_APPEND]:
                # Streamlit requires two whitespace characters in front of a newline character (markdown syntax)
                prompt += "  \n" + st.session_state[SESSION_KEY_PROMPT_APPEND]

            st.session_state[SESSION_KEY_PROMPT] = ""
            st.session_state[SESSION_KEY_PROMPT_PERPEND] = ""
            st.session_state[SESSION_KEY_PROMPT_APPEND] = ""

            # split batch prompt in multiple prompts
            prompts = prompt.split("\n\\NEWPROMPT\n")
            for prompt in prompts:

                # add prompt to context
                st.session_state[SESSION_KEY_MESSAGES].append({ ROLE: ROLE_US, MSG: prompt, MSG_FORMAT: MSG_FORMAT_TXT })

                # display message
                with st.chat_message(ROLE_US):
                    st.write(prompt)

                # run interpreter on prompt
                #run_interpreter(prompt)

                # run llm
                (llm_response, llm_execution_duration) = run_llm(prompt)
                int_input_syntax = self.conversation_manager.process_llm_response(llm_response, llm_execution_duration)

                # run interpreter on response
                run_interpreter(int_input_syntax)

        # Sidebar for parameter configuration
        with st.sidebar:
            st.title(self.ui_title)

            st.info(self.ui_init_message)

            st.subheader('LLM Settings')

            # LLM selection
            selected_llm = st.sidebar.selectbox(
                'Model', 
                sorted(self.available_models.keys()), 
                key='selected_llm')
            
            new_llm_selected = self.conversation_manager.select_llm(selected_llm)

            #st.subheader('LLM Parameters')

            llm_param_binding = self.conversation_manager.set_llm_parameters(INIT_MSG)
            
            # Create LLM UI controls
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

            # Interpreter selection
            selected_interpreter = st.sidebar.selectbox(
                'Interpreter',
                conversation_manager.INT_ID_LIST,
                key='selected_interpreter')

            new_interpreter_selected = self.conversation_manager.select_interpreter(selected_interpreter)

            int_param_binding = self.conversation_manager.set_interpreter_parameters()

            #st.subheader('Interpreter Parameters')

            # Create interpreter UI controls
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
            
            # File upload
            st.subheader('Upload Files')

            # Display file uploader
            if not "show_file_uploader" in st.session_state or st.session_state["show_file_uploader"]:
                st.session_state["file_uploader_visible"] = True
                #with st.chat_message(ROLE_AS):
                uploaded_file = st.file_uploader("Augment prompt with file contents", type=None, accept_multiple_files=False, 
                                            help="Uploads and reads UTF-8 encoded text files and allows them to be used as prompts.",
                                            on_change=show_file_uploader)
                if uploaded_file:
                    text_content = ""
                    try:
                        stio = StringIO(uploaded_file.getvalue().decode("utf-8"))
                        text_content += stio.read()
                        stio.close()
                        uploaded_file.close()
                        st.button("Submit contents", on_click=set_prompt, args=(text_content,), use_container_width=True)
                        st.button("Append contents to next prompt", on_click=append_to_next_prompt, args=(text_content,), use_container_width=True)
                        st.button("Prepend contents to next prompt", on_click=prepend_to_next_prompt, args=(text_content,), use_container_width=True)
                        text_content = ""
                    except UnicodeDecodeError:
                        st.error("Unicode decode error")
                else:
                    # uploaded file cleared
                    st.session_state[SESSION_KEY_PROMPT_APPEND] = ""
                    st.session_state[SESSION_KEY_PROMPT_PERPEND] = ""
            else:
                st.session_state["file_uploader_visible"] = False
                #st.experimental_rerun()

            st.subheader('Conversation Context')
            st.sidebar.button('Start new conversation', on_click=clear_chat_history, use_container_width=True)
            st.sidebar.button('Remove last message', on_click=remove_last_prompt_and_response, use_container_width=True)

            # end of sidebar context

        # Display messages part of the session state
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

        # read user prompt input
        user_prompt_input = st.chat_input() #st.chat_input(disabled=(len(api_key) < 1))
        
        # if there is no system-side prompt set for execution, execute the user input
        if not st.session_state[SESSION_KEY_PROMPT] and user_prompt_input:
            st.session_state[SESSION_KEY_PROMPT] = user_prompt_input

        if st.session_state[SESSION_KEY_PROMPT]:
            submit_user_prompt()

