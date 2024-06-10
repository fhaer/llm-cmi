import sys
import os

import replicate
import openai

import requests
import json
import re

API_OPENAPI = "OpenAI"
API_REPLICATE = "Replicate"
API_OLLAMA = "Ollama"

LLM_API_IDS = [
     API_OPENAPI, API_REPLICATE, API_OLLAMA
]

LLM_API_ENDPOINT_DEFAULTS = {#
    # Default Ollama API Endpoint (may be overwritten by commandline option)
    API_OLLAMA: 'http://127.0.0.1:11434/api/generate'
    # OpenAPI and Replicate endpoints are set by libraries
}

LLM_BY_ID = {
    # 1. Ollama models will be loaded at runtime
    # 2. GPT models, see https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo
    API_OPENAPI + '/gpt-4o-2024-05-13': 'gpt-4o-2024-05-13',
    API_OPENAPI + '/gpt-4-turbo-2024-04-09': 'gpt-4-turbo-2024-04-09',
    API_OPENAPI + '/gpt-4-0125-preview': 'gpt-4-0125-preview',
    API_OPENAPI + '/gpt-4-0613': 'gpt-4-0613',
    API_OPENAPI + '/gpt-3.5-turbo-0125': 'gpt-3.5-turbo-0125',
    # 3. Replicate models, see https://replicate.com/explore, https://replicate.com/mistralai, https://replicate.com/meta
    API_REPLICATE + '/mixtral-8x7B-Instruct v0.1': 'mistralai/mixtral-8x7b-instruct-v0.1',
    API_REPLICATE + '/llama3-70B-Chat': 'meta/meta-llama-3-70b-instruct',
    API_REPLICATE + '/llama2-70B-Chat': 'meta/llama-2-70b-chat',
    # TODO: Phi, Codestral
}

# Query the following models on startup (overwrites pre-defined models) 
LLM_API_QUERY_AVAILABLE_MODELS = [
     API_OLLAMA
]

PARAMETER_DEFAULTS = {
    API_OPENAPI: {
        "temperature": 0.2,
        "top_p": 0.9,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0
    },
    API_REPLICATE: {
        "temperature": 0.2,
        "top_p": 0.9,
        "max_new_tokens": 4096,
        "min_new_tokens": -1,
        "top_k": 50
        #"stop_sequences": ""
    },
    API_OLLAMA: {
        "temperature": 0.2,
        "top_p": 0.9,
        "top_k": 50
        #"num_keep": 5,
        #"seed": 42,
        #"num_predict": 100,
        #"tfs_z": 0.5,
        #"typical_p": 0.7,
        #"repeat_last_n": 33,
        #"repeat_penalty": 1.2,
        #"presence_penalty": 1.5,
        #"frequency_penalty": 1.0,
        #"mirostat": 1,
        #"mirostat_tau": 0.8,
        #"mirostat_eta": 0.6,
        #"penalize_newline": true,
        #"stop": ["\n", "user:"],
        #"numa": false,
        #"num_ctx": 4,
        #"num_batch": 2,
        #"num_gqa": 1,
        #"num_gpu": 1,
        #"main_gpu": 0,
        #"low_vram": false,
        #"f16_kv": true,
        #"logits_all": false,
        #"vocab_only": false,
        #"use_mmap": true,
        #"use_mlock": false,
        #"embedding_only": false,
        #"rope_frequency_base": 1.1,
        #"rope_frequency_scale": 0.8,
        #"num_thread": 8
    }
}

CTX_TEMPLATE = "You are a helpful assistant. You do not respond as 'user' or pretend to be 'user'. You only respond once as 'assistant'."

ROLE = "role"
ROLE_AS = "assistant"
ROLE_US = "user"

MSG = "message"
MSG_FORMAT = "format"
MSG_FORMAT_INIT = "in"
MSG_FORMAT_PROMPT = "pr"
MSG_FORMAT_RESPONSE_LLM = "re/llm"
MSG_FORMAT_RESPONSE_INT = "re/int"

class LLMApiClient:
    """Requests running a LLM through an API"""

    def __init__(self):
        print("Load LLM API client ...")

    def query_available_models(self, api_keys, api_endpoints):
        """Query available models from each API that was enabled by setting an API key or endpoint"""

        if API_OPENAPI in LLM_API_QUERY_AVAILABLE_MODELS:
            if API_OPENAPI in api_keys:
                print("Requesting available OpenAI models ...")
                openai.api_key = api_keys[API_OPENAPI]
                os.environ["REPLICATE_API_TOKEN"] = api_keys[API_OPENAPI]
                openai_models = openai.Model.list()
                if isinstance(openai_models, dict) and 'data' in openai_models.keys():
                    print("Available OpenAI GPT models:")
                    for m in openai_models['data']:
                        id = m['id']
                        if id.startswith('gpt'):
                            print(id)

        if API_REPLICATE in LLM_API_QUERY_AVAILABLE_MODELS:
            if API_REPLICATE in api_keys:
                print("Requesting available Replicate models ...")
                os.environ["REPLICATE_API_TOKEN"] = api_keys[API_REPLICATE]
                models = replicate.models.list()
                print("Available Replicate Llama and Mistral models:")
                for m in models:
                    if m.name.startswith('llama') or m.name.startswith('mistral'):
                        print(m.name, m.latest_version)

        if API_OLLAMA in LLM_API_QUERY_AVAILABLE_MODELS:
            if API_OLLAMA in api_endpoints:
                print("Requesting available Ollama models ...")
                repsponse = requests.get(api_endpoints[API_OLLAMA] + '/tags')
                m_json = []
                try:
                    m_json = repsponse.json()
                except requests.exceptions.JSONDecodeError:
                    print("API JSON Decode Error, possibly the API address set using -a is incorrect")
                if 'models' in m_json:
                    # overwrite pre-defined models
                    remove_models = []
                    for id in LLM_BY_ID.keys():
                        if id.startswith(API_OLLAMA):
                            remove_models.append(id)
                    for id in remove_models:
                        del LLM_BY_ID[id]
                    # update model list
                    for m in m_json['models']:
                        name = m['name']
                        digest = m['digest'][0:12]
                        family, parameter_size, quantization_level = "", "", ""
                        if 'details' in m.keys():
                            if 'family' in m['details'].keys():
                                family = m['details']['family']
                            if 'parameter_size' in m['details'].keys():
                                parameter_size = m['details']['parameter_size']
                            if 'quantization_level' in m['details'].keys():
                                quantization_level = m['details']['quantization_level']
                        id = "{}/{}, {}, {}, {})".format(API_OLLAMA, name.capitalize().replace(":", " ("), parameter_size, quantization_level, digest)
                        LLM_BY_ID[id] = name
                        #print("-", id, name)
                    print("Found", len(m_json['models']), "Ollama models")

    def initialize_llm(self, selected_llm, selected_llm_api_id, llm_parameters, api_key, api_endpoint):
        """Sets LLM and parameters with API keys"""

        print("Initialize LLM API client ...")

        # Store API keys in environment variables
        if selected_llm.startswith(API_OPENAPI):
            os.environ["OPENAI_API_KEY"] = api_key
        elif selected_llm.startswith(API_REPLICATE):
            os.environ["REPLICATE_API_TOKEN"] = api_key
        
        self.api_key = api_key

        self.selected_llm = selected_llm
        self.selected_llm_api_id = selected_llm_api_id

        self.llm_parameters = llm_parameters

        # Set API endpoint
        if selected_llm.startswith(API_OLLAMA) and api_endpoint:
            self.api_endpoint = api_endpoint
        elif selected_llm.startswith(API_OLLAMA):
            self.api_endpoint = LLM_API_ENDPOINT_DEFAULTS[API_OLLAMA]

        # Context returned by some APIs
        self.llm_returned_context = []

        # LLM response is streamed and not finished
        self.llm_response_ongoing = False
        self.llm_response_buffer = []

    def run_llm_replicate(self, llm_id, dialogue):
        """Run LLM with the replicate API"""

        # https://replicate.com/meta/llama-2-70b-chat
        api_parameters = { "prompt": f"{dialogue} {ROLE_AS}: " } #"repetition_penalty": 1, "stop_sequences": ""

        # add parameters
        for p in self.llm_parameters.keys():
            api_parameters[p] = self.llm_parameters[p]

        #print(self.llm_parameters)
        #print(api_parameters)

        response = replicate.stream(llm_id, input=api_parameters)
        return response

    def run_llm_openai(self, llm_id, dialogue):
        """Run LLM with the OpenAI API"""

        # https://platform.openai.com/docs/api-reference/chat/create

        api_parameters = {
            "model": llm_id,
            "messages": dialogue,
            "stream": True
        }

        # add parameters
        for p in self.llm_parameters.keys():
            api_parameters[p] = self.llm_parameters[p]

        #print(self.llm_parameters)
        #print(api_parameters)

        openai.api_key = self.api_key

        result = openai.ChatCompletion.create(**api_parameters)
        return result

    def run_llm_rest_ollama(self, llm_id, dialogue):
        """Run LLM with the given Rest API"""

        # https://github.com/jmorganca/ollama/blob/main/docs/api.md
        # https://github.com/jmorganca/ollama/blob/main/docs/modelfile.md#valid-parameters-and-values
        api_parameters = {
            'model': llm_id, 
            'prompt': dialogue,
            'stream': True,
            'options': {}
        }

        if len(self.llm_returned_context) > 0:
            api_parameters['context'] = self.llm_returned_context

        # add parameters
        for p in self.llm_parameters.keys():
            api_parameters['options'][p] = self.llm_parameters[p]

        response = requests.post(self.api_endpoint + '/generate', json=api_parameters, stream=True)
        return response

    # Function for generating LLaMA2 llm_response
    def request_run_llm_llama2(self, context):
        """Run the Llama 2 LLM with the provided context, including the prompt as last message, in a suitable dialogue format"""

        dialogue = CTX_TEMPLATE + "\\n\\n"
        for message in context:
            if MSG_FORMAT in message.keys() and ROLE in message.keys():
                if message[MSG_FORMAT] != MSG_FORMAT_RESPONSE_INT:
                    role = message[ROLE]
                    if role == ROLE_US or role == ROLE_AS:
                        # include user and assistant messages in the prompt, 
                        # including generated code, not including interpreter output
                        dialogue += role + ": " + message[MSG] + "\\n\\n"
                    #elif role == ROLE_INT:
                        # do not include interpreter output

        items = self.run_llm_replicate(self.selected_llm_api_id, dialogue)
        item_function = lambda item: str(item)
        #result = [f"Echo: {prompt}"]
        return (items, item_function)

    # Function for generating llm_response using replicate models without specific functions
    def request_run_llm_replicate(self, context):
        """Run a Replicate LLM with the provided context, including the prompt as last message, in a suitable dialogue format"""

        dialogue = CTX_TEMPLATE + "\n\n"
        for message in context:
            if MSG_FORMAT in message.keys() and ROLE in message.keys():
                if message[MSG_FORMAT] != MSG_FORMAT_RESPONSE_INT:
                    role = message[ROLE]
                    if role == ROLE_US or role == ROLE_AS:
                        # include user and assistant messages in the prompt, 
                        # including generated code, not including interpreter output
                        dialogue += role + ": " + message[MSG] + "\n\n"
                    #elif role == ROLE_INT:
                        # do not include interpreter output

        items = self.run_llm_replicate(self.selected_llm_api_id, dialogue)
        item_function = lambda item: str(item)
        #result = [f"Echo: {prompt}"]
        return (items, item_function)

    def request_run_llm_ollama_parse_response(self, response):
        """Parses JSON responses from Ollama"""

        # Check if the response is complete or still ongoing
        response_last = response.decode('utf-8')
        if response_last.endswith('}\n') or response_last.endswith('}'):
            # response is complete
            response_text = ""
            for response_buffered in self.llm_response_buffer:
                response_text += response_buffered
            response_text += response_last

            self.llm_response_ongoing = False
            self.llm_response_buffer = []

            try:
                jsonr = json.loads(response_text)
                for k in ['prompt_eval_duration', 'eval_duration']:
                    if k in jsonr:
                        print("{}: {}".format(k, jsonr[k]))
                if 'context' in jsonr:
                    self.llm_returned_context = jsonr['context']
                if 'response' in jsonr:
                    return jsonr['response']
                if 'error' in jsonr:
                    return "*LLM API returned error: {}*".format(jsonr['error'])
            except json.decoder.JSONDecodeError:
                return ''

        elif not self.llm_response_ongoing and response_last.startswith('{'):
            # response is beginning
            self.llm_response_ongoing = True
            self.llm_response_buffer.append(response_last)
            return ''
        elif self.llm_response_ongoing:
            # response is ongoing
            self.llm_response_ongoing = True
            self.llm_response_buffer.append(response_last)
            return ''

        return ''


    # Function for generating an llm_response using Ollama
    def request_run_llm_ollama(self, prompt):
        """Run an LLM with Ollama with the provided context, including the prompt as last message, in a suitable dialogue format"""

        items = self.run_llm_rest_ollama(self.selected_llm_api_id, prompt)
        item_function = lambda item: self.request_run_llm_ollama_parse_response(item)

        #result = [f"Echo: {prompt}"]
        return (items, item_function)

    def request_run_llm_chatgpt4(self, context):
        """Run a ChatGPT LLM with the provided context, including the prompt as last message, in a suitable dialogue format"""

        dialogue = []
        for message in context:
            if MSG_FORMAT in message.keys() and ROLE in message.keys():
                if message[MSG_FORMAT] != MSG_FORMAT_RESPONSE_INT:
                    role = message[ROLE]
                    if role == ROLE_US or role == ROLE_AS:
                        dialogue.append({"role": message[ROLE], "content": message[MSG]})

        items = self.run_llm_openai(self.selected_llm_api_id, dialogue)
        item_function = lambda item: item.choices[0].delta.get("content", "")
        #result = [f"Echo: {prompt}"]
        return (items, item_function)

    def request_run_prompt(self, context, prompt):
        """Runs the provided prompt or a context that includes the prompt as last message"""

        if self.selected_llm.startswith(API_REPLICATE + '/Llama2'):
            return self.request_run_llm_llama2(context)
        elif self.selected_llm.startswith(API_REPLICATE):
            return self.request_run_llm_replicate(context)
        elif self.selected_llm.startswith(API_OPENAPI):
            return self.request_run_llm_chatgpt4(context)
        elif self.selected_llm.startswith(API_OLLAMA):
            return self.request_run_llm_ollama(prompt)

    def clear_returned_context(self):
        self.llm_returned_context = []
