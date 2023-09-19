import sys

from llama_cpp import Llama

RUNTIME_LLAMA_CPP = "Llama.cpp"

LLM_RUNTIME_IDS = [
     RUNTIME_LLAMA_CPP
]

LLM_BY_ID = {
    RUNTIME_LLAMA_CPP + '/WizardLM-1.1-13B-GGML': 'models/wizardlm-13b-v1.1.ggmlv3.q4_1.bin',
    RUNTIME_LLAMA_CPP + '/Llama2-13B-GGML': 'models/llama-2-13b-chat.ggmlv3.q5_K_M.bin',
    RUNTIME_LLAMA_CPP + '/OpenOrca-Platypus2-13B-GGML': 'models/openorca-platypus2-13b.ggmlv3.q5_K_M.bin'
}

PARAMETER_DEFAULTS = {
    RUNTIME_LLAMA_CPP: {
        "temperature": 0.2,
        "top_p": 0.9,
        "top_k": 50,
        "n_tokens_max": 4096,
        "n_tokens_min": -1,
        "n_ctx": 4096
    }
}

CTX_TEMPLATE = "You are a helpful assistant. You do not respond as 'user' or pretend to be 'user'. You only respond once as 'assistant'."

ROLE = "role"
ROLE_AS = "assistant"
ROLE_US = "user"

MSG = "message"
MSG_FORMAT = "format"
MSG_FORMAT_TXT = "text"

class LLMRuntime:
    """Runs locally a LLM runtime such as llama.cpp"""

    def __init__(self):
        print("Load LLM Runtime ...")
        self.selected_llm = None
        self.llm_parameters = None
        self.llm_files = None
        self.llama_cpp = None

    def load_llm_files(self, selected_llm, llm_parameters):
        """Load LLM files and initialize with runtime"""

        print("Load LLM Files ...")

        self.selected_llm = selected_llm
        self.llm_parameters = llm_parameters

        self.llm_files = LLM_BY_ID[selected_llm]
        print(self.llm_files)
        self.llama_cpp = Llama(
            model_path=self.llm_files, 
            n_ctx=self.llm_parameters["n_ctx"]
            )

    def run_llm_llama_cpp(self, context, prompt):
        """Run llama.cpp with the given context as message array. The prompt is assumed as last message of the context."""

        dialogue = CTX_TEMPLATE + "\\n\\n"
        for message in context:
            if MSG_FORMAT in message.keys() and ROLE in message.keys():
                if message[MSG_FORMAT] == MSG_FORMAT_TXT:
                    role = message[ROLE]
                    if role == ROLE_US or role == ROLE_AS:
                        dialogue += role + ": " + message[MSG] + "\\n\\n"

        response = self.llama_cpp(f"{dialogue} {ROLE_AS}: ", 
                                  max_tokens=self.llm_parameters["n_tokens_max"], 
                                  stop=[ROLE_US + ":", "\n"], 
                                  echo=True
                                  )
        
        items = [response]
        item_function = lambda item: item["choices"][0]["text"]
        return (items, item_function)

    def run_prompt(self, prompt):
        """
        Executes the prompt. Returns the response as tuple (items_wrapped, item_function) where item_function is a 
        lambda function extracting the wrapped response items.
        """
        
        (items_wrapped, item_function) = self.run_llm_llama_cpp(prompt)
        return (items_wrapped, item_function)

