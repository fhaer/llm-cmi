# LLM Conceptual Model Interpreter

Prototype implementation of a model interpreter for generating and rendering conceptual models in a conversational user interface. The prototype supports code generation with GPT-4 and Llama 2 and the rendering of <a href="https://plantuml.com/">PlantUML</a> and <a href="https://graphs.grevian.org/">Graphviz</a> code using <a href="https://plantweb.readthedocs.io/">Plantweb</a>. The implementation is based on Python 3.11 with the <a href="https://streamlit.io/">Streamlit</a> framework.

Note: The prototype is only intended as a feasibility demonstration.

Requirements: 
- Python 3.11 with the packages listed in requirements.txt
- API keys for OpenAI and/or Replicate set with the "-a" option shown below
- For local inference, llama.cpp is required and LLM files need to be present in a subdirectory "models"

Usage, parameters and further details:

```
> python3 cmi.py --help
CMI Test Environment v0.1

Usage: cmi.py [-h|--help] [-a|--api <api_id>:<api_key>[:api_endpoint]]* [-p|--port <ui_port>]

<api_id> = OpenAI | Replicate | Ollama

Supported local LLM runtime:
- Llama.cpp

Supported LLM API clients:
- OpenAI
- Replicate
- Ollama

Supported LLMs:
- Ollama/Neural-Chat
- Ollama/OpenChat
- Ollama/Mistral
- Ollama/OpenHermes-2.5-Mistral
- Ollama/Llama2
- Ollama/Llama2-70B-Chat
- Ollama/Stable-Beluga
- Ollama/Stable-Beluga-70B
- Ollama/Vicuna
- Ollama/Vicuna-33B
- Ollama/Wizard-Math
- Ollama/Wizard-Math-70B
- Ollama/Yi
- Ollama/Yi-34B
- Ollama/Yi-34B-Q4_K_M
- Ollama/Zephyr
- OpenAI/gpt-4
- OpenAI/gpt-3.5-turbo
- OpenAI/gpt-3.5-turbo-16k
- OpenAI/gpt-3.5-turbo-instruct
- Replicate/Llama2-70B-Chat
- Replicate/Llama2-70B
- Replicate/Llama2-13B
- Replicate/Llama2-7B
- Replicate/Mistral-7B-Instruct
- Replicate/CodeLlama-34B-Instruct-GGUF
- Replicate/WizardCoder-Python-34B
- Replicate/CodeLlama-13B-Instruct
- Replicate/Falcon-40B-Instruct
- Llama.cpp/WizardLM-1.1-13B-GGML
- Llama.cpp/Llama2-13B-GGML
- Llama.cpp/OpenOrca-Platypus2-13B-GGML

Supported Interpreters:
- Plantweb/PlantUML
- Plantweb/Graphviz

Example Usage:
- Run with API keys for OpenAI and Replicate:
  cmi.py -a OpenAI:INSERT_KEY -a Replicate:INSERT_KEY
- Run with a specific Ollama endpoint:
  cmi.py -a Ollama::'http://INSERT_HOST:INSERT_PORT/api/generate'

The web-based UI will be started at port <ui_port>, default: 8501
```

Example:

<img src="https://raw.githubusercontent.com/fhaer/llm-cmi/master/cmi-graphviz.png" width="100%" />

#### Related Publication

Härer, Felix (2023): Conceptual Model Interpreter for Large Language Models, accepted for: ER Forum 2023, 42nd International Conference on Conceptual Modeling (ER 2023), November 6-9, 2023, Lisbon, PT. 
