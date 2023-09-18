import sys
import os

import replicate
import openai

API_OPENAPI = "OpenAI"
API_REPLICATE = "Replicate"

LLM_API_IDS = [
     API_OPENAPI, API_REPLICATE
]

LLM_BY_ID = {
    API_OPENAPI + '/gpt-4': 'gpt-4',
    API_OPENAPI + '/gpt-4-32k': 'gpt-4-32k',
    API_OPENAPI + '/gpt-3.5-turbo': 'gpt-3.5-turbo',
    API_OPENAPI + '/gpt-3.5-turbo-16k': 'gpt-3.5-turbo-16k',
    API_REPLICATE + '/Llama2-70B-Chat': 'replicate/llama-2-70b-chat:2796ee9483c3fd7aa2e171d38f4ca12251a30609463dcfd4cd76703f22e96cdf',
    API_REPLICATE + '/Llama2-70B': 'replicate/llama70b-v2-chat:e951f18578850b652510200860fc4ea62b3b16fac280f83ff32282f87bbd2e48', 
    API_REPLICATE + '/Llama2-13B': 'a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5', 
    API_REPLICATE + '/Llama2-7B': 'a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea', 
    API_REPLICATE + '/Code-Llama-34B': 'replicate/codellama-34b:0666717e5ead8557dff55ee8f11924b5c0309f5f1ca52f64bb8eec405fdb38a7'
}

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
    }
}

CTX_TEMPLATE = "You are a helpful assistant. You do not respond as 'user' or pretend to be 'user'. You only respond once as 'assistant'."

ROLE = "role"
ROLE_AS = "assistant"
ROLE_US = "user"

MSG = "message"
MSG_FORMAT = "format"
MSG_FORMAT_TXT = "text"

class LLMApiClient:

    def __init__(self):
        print("Load LLM API client ...")


    def initialize_llm(self, selected_llm, selected_llm_api_id, llm_parameters, api_key):
        print("Initialize LLM API client ...")

        if selected_llm.startswith(API_OPENAPI):
            os.environ["OPENAI_API_KEY"] = api_key
        elif selected_llm.startswith(API_REPLICATE):
            os.environ["REPLICATE_API_TOKEN"] = api_key
        
        self.api_key = api_key

        self.selected_llm = selected_llm
        self.selected_llm_api_id = selected_llm_api_id

        self.llm_parameters = llm_parameters

    def run_llm_replicate(self, llm_id, dialogue):
        print(self.llm_parameters)
        # https://replicate.com/meta/llama-2-70b-chat
        response = replicate.run(llm_id,
                            input={"prompt": f"{dialogue} {ROLE_AS}: ",
                                    "temperature": self.llm_parameters["temperature"], 
                                    "top_k": self.llm_parameters["top_k"],  
                                    "top_p": self.llm_parameters["top_p"],  
                                    "max_new_tokens": self.llm_parameters["max_new_tokens"], 
                                    "min_new_tokens": self.llm_parameters["min_new_tokens"], 
                                    "repetition_penalty": 1,
                                    "stop_sequences": ""
                                    })
        return response

    def run_llm_openai(self, llm_id, dialogue):
        print(self.llm_parameters)
        # https://platform.openai.com/docs/api-reference/chat/create
        result = openai.ChatCompletion.create(
            model=llm_id,
            messages=dialogue,
            stream=True,
            temperature=self.llm_parameters["temperature"], 
            top_p=self.llm_parameters["top_p"],
            # presence_penalty=0, 
            # frequency_penalty=0
        )
        return result

    # Function for generating LLaMA2 llm_response
    def request_run_llm_llama2(self, context):
        #set_default_parameters_llama2()
        dialogue = CTX_TEMPLATE + "\\n\\n"
        for message in context:
            if MSG_FORMAT in message.keys() and ROLE in message.keys():
                if message[MSG_FORMAT] == MSG_FORMAT_TXT:
                    role = message[ROLE]
                    if role == ROLE_US or role == ROLE_AS:
                        dialogue += role + ": " + message[MSG] + "\\n\\n"
                    #elif role == ROLE_INT:
                        #dialogue += ROLE_AST + ": " + message + "\\n\\n"

        items = self.run_llm_replicate(self.selected_llm_api_id, dialogue)
        item_function = lambda item: item
        #result = [f"Echo: {prompt}"]
        return (items, item_function)

    def request_run_llm_chatgpt4(self, context):
        dialogue = []
        for message in context:
            if MSG_FORMAT in message.keys() and ROLE in message.keys():
                if message[MSG_FORMAT] == MSG_FORMAT_TXT:
                    role = message[ROLE]
                    if role == ROLE_US or role == ROLE_AS:
                        dialogue.append({"role": message[ROLE], "content": message[MSG]})

        items = self.run_llm_openai(self.selected_llm_api_id, dialogue)
        item_function = lambda item: item.choices[0].delta.get("content", "")
        #result = [f"Echo: {prompt}"]
        return (items, item_function)

    def request_run_prompt(self, context):
        if self.selected_llm.startswith(API_REPLICATE):
            return self.request_run_llm_llama2(context)
        elif self.selected_llm.startswith(API_OPENAPI):
            return self.request_run_llm_chatgpt4(context)

