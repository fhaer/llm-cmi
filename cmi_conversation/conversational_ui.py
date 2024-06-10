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

SESSION_KEY_NEXT_PROMPT = "prompt/message"
SESSION_KEY_NEXT_PROMPT_PERPEND = "prompt/message/prepend"
SESSION_KEY_NEXT_PROMPT_APPEND = "prompt/message/append"

SESSION_KEY_NEXT_INT_INPUT = "int/input"

ROLE = "role"
ROLE_AS = "assistant"
ROLE_US = "user"
ROLE_IN = "interpreter"

MSG = "message"
SRC = "source"
MSG_FORMAT = "format"
MSG_FORMAT_INIT = "in"
MSG_FORMAT_PROMPT = "pr"
MSG_FORMAT_RESPONSE_LLM = "re/llm"
MSG_FORMAT_RESPONSE_LLM_TXT = "re/llm/txt"
MSG_FORMAT_RESPONSE_LLM_CODE = "re/llm/code"
MSG_FORMAT_RESPONSE_INT = "re/int"
MSG_FORMAT_RESPONSE_INT_TXT = "re/int/txt"
MSG_FORMAT_RESPONSE_INT_IMG = "re/int/img"
MSG_RERUN_LLM = "rerun/llm"
MSG_RERUN_INT = "rerun/int"

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
        self.message_id = 0

    def set_available_models(self, models):
        self.available_models = models

    def set_available_interpreters(self, interpreters):
        self.available_interpreters = interpreters

    def trigger_update(self, message):
        st.toast(message)
        st.rerun()

    def update_web_ui(self):
        """Updates the web UI with selectable LLMs, interpreters, current parameters, and messages of the conversation"""

        # App title
        st.set_page_config(page_title=self.ui_title)
        
        # Initialize session storage for messages and prompts
        if SESSION_KEY_MESSAGES not in st.session_state.keys():
            st.session_state[SESSION_KEY_MESSAGES] = [ {ROLE: ROLE_AS, MSG: INIT_MSG, MSG_FORMAT: MSG_FORMAT_INIT} ]
        if SESSION_KEY_NEXT_PROMPT not in st.session_state.keys():
            st.session_state[SESSION_KEY_NEXT_PROMPT] = ""
        if SESSION_KEY_NEXT_PROMPT_APPEND not in st.session_state.keys():
            st.session_state[SESSION_KEY_NEXT_PROMPT_APPEND] = ""
        if SESSION_KEY_NEXT_PROMPT_PERPEND not in st.session_state.keys():
            st.session_state[SESSION_KEY_NEXT_PROMPT_PERPEND] = ""
        if SESSION_KEY_NEXT_INT_INPUT not in st.session_state.keys():
            st.session_state[SESSION_KEY_NEXT_INT_INPUT] = ""
        if MSG_RERUN_LLM not in st.session_state.keys():
            st.session_state[MSG_RERUN_LLM] = False
        if MSG_RERUN_INT not in st.session_state.keys():
            st.session_state[MSG_RERUN_INT] = ""

        # Remove all messages
        def clear_chat_history():
            st.session_state[SESSION_KEY_MESSAGES] = [ {ROLE: ROLE_AS, MSG: INIT_MSG, MSG_FORMAT: MSG_FORMAT_INIT} ]
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
            st.session_state[SESSION_KEY_NEXT_PROMPT_PERPEND] = prepend_message
            st.toast("File contents will be prepended to the next prompt submission")

        # Append text to the next prompt submitted by the user
        def append_to_next_prompt(append_message):
            st.session_state[SESSION_KEY_NEXT_PROMPT_APPEND] = append_message
            st.toast("File contents will be appended to the next prompt submission")
       
        # At the next UI update, run the given prompt
        def schedule_llm_prompt_for_next_run(message):
            st.session_state[SESSION_KEY_NEXT_PROMPT] = message
       
        # At the next UI update, run the interpreter
        def schedule_int_input_for_next_run(int_input):
            st.session_state[SESSION_KEY_NEXT_INT_INPUT] = int_input
       
        # Enables displaying the file uploader
        def show_file_uploader():
            if not "file_uploader_visible" in st.session_state or not st.session_state["file_uploader_visible"]:
                st.session_state["show_file_uploader"] = True
                
        # Disables displaying the file uploader
        def hide_file_uploader():
            st.session_state["show_file_uploader"] = False

        def insert_llm_response(placeholder, llm_response, source, allow_rerun):
            if placeholder is None:
                with st.expander("LLM Response", expanded=False):
                    placeholder = st.empty()
                    placeholder.markdown(llm_response)
                            
            self.message_id += 1

            if source is None:
                if allow_rerun:
                    st.session_state[MSG_RERUN_INT] = None
                    if self.conversation_manager.is_int_selected():
                        with st.expander("Edit LLM Response"):
                            st.session_state[MSG_RERUN_INT] = st.text_area("Edit:", height=400, value=llm_response.lstrip())
                        st.markdown("No model source code could be parsed from the LLM Response. Please re-run the LLM or edit the response and re-run the interpreter.")
                    if self.conversation_manager.is_int_selected():
                        col1, col2 = st.columns(2)
                        col1.button("Re-run LLM", on_click=remove_responses_and_rerun_llm, key="retry/llm/" + str(self.message_id), use_container_width=True)
                        col2.button("Re-run interpreter", on_click=remove_int_response_and_rerun_int, key="retry/int/" + str(self.message_id), use_container_width=True, disabled=(not self.conversation_manager.is_int_selected()))
                    else:
                        st.button("Re-run LLM", on_click=remove_responses_and_rerun_llm, key="retry/llm/" + str(self.message_id), use_container_width=True)
            else:
                st.session_state[MSG_RERUN_INT] = None
                with st.expander("Model Source Code"):
                    if allow_rerun:
                        st.session_state[MSG_RERUN_INT] = st.text_area("Edit:", height=400, value=source)
                    else:
                        st.markdown(f"```\n{source}\n```")
                if allow_rerun:
                    if self.conversation_manager.is_int_selected():
                        col1, col2 = st.columns(2)
                        col1.button("Re-run LLM", on_click=remove_responses_and_rerun_llm, key="retry/llm/" + str(self.message_id), use_container_width=True)
                        col2.button("Re-run interpreter", on_click=remove_int_response_and_rerun_int, key="retry/int/" + str(self.message_id), use_container_width=True, disabled=(not self.conversation_manager.is_int_selected()))
                    else:
                        st.button("Re-run LLM", on_click=remove_responses_and_rerun_llm, key="retry/llm/" + str(self.message_id), use_container_width=True)

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
                        with st.expander("LLM Response", expanded=True):
                            #rerun_text = st.text_area("Edit:", height=400, value=llm_response)
                            #st.text("")
                            placeholder = st.empty()
                            for item in items_wrapped:
                                llm_response += item_function(item)
                                placeholder.markdown(llm_response + "▌")
                            t_stop = perf_counter_ns()
                            execution_duration = (t_stop-t_start)
                            print("LLM total execution duration [ns]:", execution_duration)
                        # get and store source
                        source = self.conversation_manager.process_llm_response(llm_response)
                        st.session_state[SESSION_KEY_MESSAGES][-1][SRC] = source
                        # show response
                        insert_llm_response(placeholder, llm_response, source, True)
                    except requests.exceptions.ChunkedEncodingError as e:
                        placeholder.markdown(e)
                        st.button("Retry", on_click=remove_responses_and_rerun_llm, key="retry/llm/placeholder/error")

            # append response to session state
            message = {ROLE: ROLE_AS, MSG: llm_response, MSG_FORMAT: MSG_FORMAT_RESPONSE_LLM_TXT}
            st.session_state[SESSION_KEY_MESSAGES].append(message)

            return (llm_response, execution_duration)

        # Add interpreter output to session state
        def append_interpreter_output(text_output=None, image_output=None):
            if text_output:
                message = {ROLE: ROLE_IN, MSG: text_output, MSG_FORMAT: MSG_FORMAT_RESPONSE_INT_TXT}
                st.session_state[SESSION_KEY_MESSAGES].append(message)
            if image_output:
                #print(image_output)
                message = {ROLE: ROLE_IN, MSG: image_output, MSG_FORMAT: MSG_FORMAT_RESPONSE_INT_IMG}
                st.session_state[SESSION_KEY_MESSAGES].append(message)

        # Execute interpreter
        def run_interpreter():

            if self.conversation_manager.is_int_selected() and st.session_state[SESSION_KEY_NEXT_INT_INPUT]:

                input_syntax = st.session_state[SESSION_KEY_NEXT_INT_INPUT]
                st.session_state[SESSION_KEY_NEXT_INT_INPUT] = ""

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
                        #st.button("Retry", on_click=remove_int_response_and_rerun_int, args=(input_syntax,), key="retry/int/placeholder/invalid")

        # Submit user-provided prompt
        def submit_user_prompt():

            if not self.conversation_manager.is_llm_selected():
                st.session_state[SESSION_KEY_NEXT_PROMPT] = ""
            else:

                prompt = ""

                # construct prompt
                if st.session_state[SESSION_KEY_NEXT_PROMPT_PERPEND]:
                    # Streamlit requires two whitespace characters in front of a newline character (markdown syntax)
                    prompt = st.session_state[SESSION_KEY_NEXT_PROMPT_PERPEND] + "  \n"

                prompt += st.session_state[SESSION_KEY_NEXT_PROMPT]

                if st.session_state[SESSION_KEY_NEXT_PROMPT_APPEND]:
                    # Streamlit requires two whitespace characters in front of a newline character (markdown syntax)
                    prompt += "  \n" + st.session_state[SESSION_KEY_NEXT_PROMPT_APPEND]

                st.session_state[SESSION_KEY_NEXT_PROMPT] = ""
                st.session_state[SESSION_KEY_NEXT_PROMPT_PERPEND] = ""
                st.session_state[SESSION_KEY_NEXT_PROMPT_APPEND] = ""

                # split batch prompt in multiple prompts
                prompts = prompt.split("\n\\NEWPROMPT\n")
                for prompt in prompts:

                    if not st.session_state[MSG_RERUN_LLM]:
                        # add prompt to context
                        st.session_state[SESSION_KEY_MESSAGES].append({ ROLE: ROLE_US, MSG: prompt, MSG_FORMAT: MSG_FORMAT_PROMPT })
                        # display prompt message
                        with st.chat_message(ROLE_US):
                            st.write(prompt)
                    st.session_state[MSG_RERUN_LLM] = False

                    # run llm
                    (llm_response, llm_execution_duration) = run_llm(prompt)
                    self.conversation_manager.record_llm_response(llm_response, llm_execution_duration)
                    int_input_syntax = self.conversation_manager.process_llm_response(llm_response)

                    # store source
                    st.session_state[SESSION_KEY_MESSAGES][-1][SRC] = int_input_syntax
                    
                    # run interpreter on response
                    schedule_int_input_for_next_run(int_input_syntax)
                    run_interpreter()

                st.rerun()

        # Remove the last interpreter and LLM answers and re-run the LLM and interpreter
        def remove_responses_and_rerun_llm():
            # remove response (from interpreter)
            while len(st.session_state[SESSION_KEY_MESSAGES]) > 0 and st.session_state[SESSION_KEY_MESSAGES][-1][MSG_FORMAT].startswith(MSG_FORMAT_RESPONSE_INT):
                st.session_state[SESSION_KEY_MESSAGES] = st.session_state[SESSION_KEY_MESSAGES][0:-1]
                self.conversation_manager.remove_last_message()
            # remove response (from LLM)
            while len(st.session_state[SESSION_KEY_MESSAGES]) > 0 and st.session_state[SESSION_KEY_MESSAGES][-1][MSG_FORMAT].startswith(MSG_FORMAT_RESPONSE_LLM):
                st.session_state[SESSION_KEY_MESSAGES] = st.session_state[SESSION_KEY_MESSAGES][0:-1]
                self.conversation_manager.remove_last_message()
            # get last prompt and re-run
            if st.session_state[SESSION_KEY_MESSAGES][-1][MSG_FORMAT] == MSG_FORMAT_PROMPT:
                last_prompt = st.session_state[SESSION_KEY_MESSAGES][-1][MSG]
                st.session_state[MSG_RERUN_LLM] = True
                schedule_llm_prompt_for_next_run(last_prompt)

        # Remove the last interpreter response and re-run the interpreter
        def remove_int_response_and_rerun_int():
            if self.conversation_manager.is_int_selected():
                int_input = st.session_state[MSG_RERUN_INT]
                # remove response (from interpreter)
                while len(st.session_state[SESSION_KEY_MESSAGES]) > 0 and st.session_state[SESSION_KEY_MESSAGES][-1][MSG_FORMAT].startswith(MSG_FORMAT_RESPONSE_INT):
                    st.session_state[SESSION_KEY_MESSAGES] = st.session_state[SESSION_KEY_MESSAGES][0:-1]
                    self.conversation_manager.remove_last_message()
                # set interpreter input and re-run
                if st.session_state[SESSION_KEY_MESSAGES][-1][MSG_FORMAT].startswith(MSG_FORMAT_RESPONSE_LLM):
                    # store input as source code
                    st.session_state[SESSION_KEY_MESSAGES][-1][SRC] = int_input
                    schedule_int_input_for_next_run(int_input)


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
                sorted(self.available_interpreters.keys()),
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
                        st.button("Submit contents", on_click=schedule_llm_prompt_for_next_run, args=(text_content,), use_container_width=True)
                        st.button("Append contents to next prompt", on_click=append_to_next_prompt, args=(text_content,), use_container_width=True)
                        st.button("Prepend contents to next prompt", on_click=prepend_to_next_prompt, args=(text_content,), use_container_width=True)
                        text_content = ""
                    except UnicodeDecodeError:
                        st.error("Unicode decode error")
                else:
                    # uploaded file cleared
                    st.session_state[SESSION_KEY_NEXT_PROMPT_APPEND] = ""
                    st.session_state[SESSION_KEY_NEXT_PROMPT_PERPEND] = ""
            else:
                st.session_state["file_uploader_visible"] = False
                #st.rerun()

            st.subheader('Conversation Context')
            st.sidebar.button('Start new conversation', on_click=clear_chat_history, use_container_width=True)
            st.sidebar.button('Remove last prompt and response', on_click=remove_last_prompt_and_response, use_container_width=True)

            # end of sidebar context

        # Display messages part of the session state
        c = 0
        for message in st.session_state[SESSION_KEY_MESSAGES]:
            self.message_id += 1
            avatar = None
            if message[ROLE] == ROLE_IN:
                avatar = AVATAR_INTER
            with st.chat_message(message[ROLE]):
                if MSG_FORMAT in message.keys():
                    if message[MSG_FORMAT] == MSG_FORMAT_INIT or message[MSG_FORMAT] == MSG_FORMAT_PROMPT:
                        placeholder = st.empty()
                        placeholder.write(message[MSG])
                        #placeholder.button("Edit", on_click=edit_prompt, key="edit/prompt/" + str(c))
                        #placeholder.button("Retry", on_click=rerun_llm, key="retry/int/" + str(c))
                    if message[MSG_FORMAT] == MSG_FORMAT_RESPONSE_LLM_TXT:
                        #placeholder.write(message[MSG])
                        allow_rerun = False
                        if c >= len(st.session_state[SESSION_KEY_MESSAGES]) - 2 and not st.session_state[MSG_RERUN_LLM]:
                            allow_rerun = True
                        insert_llm_response(None, message[MSG], message[SRC], allow_rerun)
                    if message[MSG_FORMAT] == MSG_FORMAT_RESPONSE_INT_IMG:
                        placeholder = st.empty()
                        placeholder.image(message[MSG])
                        #placeholder.button("Retry", on_click=remove_int_response_and_rerun_int, args=(text), key="retry/int/" + str(c))
                    if message[MSG_FORMAT] == MSG_FORMAT_RESPONSE_INT_TXT:
                        placeholder = st.empty()
                        placeholder.write(message[MSG])
                        #placeholder.button("Retry", on_click=remove_int_response_and_rerun_int, args=(text), key="retry/int/" + str(self.message_id))
                else:
                    print("Unknown format: " + str(message.keys()))
                    st.write(message[MSG])
            c += 1

        # read user prompt input
        user_prompt_input = st.chat_input() #st.chat_input(disabled=(len(api_key) < 1))
        
        # if there is no system-side prompt set for execution, execute the user input
        if not st.session_state[SESSION_KEY_NEXT_PROMPT] and user_prompt_input:
            st.session_state[SESSION_KEY_NEXT_PROMPT] = user_prompt_input

        if st.session_state[SESSION_KEY_NEXT_PROMPT]:
            submit_user_prompt()

        if st.session_state[SESSION_KEY_NEXT_INT_INPUT]:
            run_interpreter()
