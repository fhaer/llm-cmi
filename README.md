# LLM Conceptual Model Interpreter

Prototype implementation of a model interpreter for generating and rendering conceptual models in a conversational user interface. The prototype supports code generation with GPT-4 and Llama 2 and the rendering of <a href="https://plantuml.com/">PlantUML</a> and <a href="https://graphs.grevian.org/">Graphviz</a> code using <a href="https://plantweb.readthedocs.io/">Plantweb</a>. The implementation is based on Python 3.11 with the <a href="https://streamlit.io/">Streamlit</a> framework.

Note: The prototype is only intended as a feasibility demonstration.

Requirements: 
- Python 3.11 with the packages listed in requirements.txt
- API keys for OpenAI and/or Replicate set with the "-a" option shown below
- For local inference, an Ollama endpoint needs to be set with the "-a" option

Usage, parameters and further details:

```
> python3 cmi.py --help
CMI Test Environment v0.1

Usage: cmi.py [-h|--help] [-a|--api <api_id>:<api_key>[:api_endpoint]]* [-p|--port <ui_port>]

<api_id> = OpenAI | Replicate | Ollama | BPMN-Auto-Layout

Supported LLM Clients:
- OpenAI
- Replicate
- Ollama

Supported Interpreters:
- BPMN-Auto-Layout/BPMN-XML
- Plantweb/PlantUML
- Plantweb/Graphviz

Supported LLMs:
- Ollama/Llama2 (70b-chat-q5_k_m, 69B, Q5_K_M, 2e12d2211dd5)
- Ollama/Mistral (7b-instruct-q5_k_m, 7B, Q5_K_M, 8397c99c426f)
- Ollama/Mixtral (8x7b-instruct-v0.1-q5_k_m, 47B, Q5_K_M, 58b4d0644efd)
- Ollama/Neural-chat (7b-v3.3-q5_k_m, 7B, Q5_K_M, 6e7f6242bbec)
- Ollama/Openchat (7b-v3.5-1210-q5_k_m, 7B, Q5_K_M, 64e4cb9bb506)
- Ollama/Openhermes (7b-mistral-v2.5-q5_k_m, 7B, Q5_K_M, 16eab97b0cd1)
- Ollama/Orca2 (13b-q5_k_m, 13B, Q5_K_M, d5e443067226)
- Ollama/Phi (2.7b-chat-v2-q5_k_m, 3B, Q5_K_M, 4dbc1775ae76)
- Ollama/Qwen (14b-chat-v1.5-q5_k_m, 14B, Q5_K_M, ba0e61d66b27)
- Ollama/Qwen (72b-chat-v1.5-q5_k_m, 72B, Q5_K_M, 13a773260811)
- Ollama/Solar (10.7b-instruct-v1-q5_k_m, 11B, Q5_K_M, ef538f3193f7)
- Ollama/Stable-beluga (13b-q5_k_m, 13B, Q5_K_M, 72350608e9fc)
- Ollama/Stablelm2 (1.6b-zephyr-q4_k_m, 2B, Q4_K_M, 2f41c2ec1f16)
- Ollama/Yi (34b-chat-q5_k_m, 34B, Q5_K_M, 56f40aebe6c6)
- OpenAI/gpt-4-0125-preview
- OpenAI/gpt-4-1106-preview
- OpenAI/gpt-4-0613
- OpenAI/gpt-3.5-turbo-0125
- OpenAI/gpt-3.5-turbo-1106
- Replicate/Mistral-7B-Instruct v0.2 79052a3adbba
- Replicate/Mixtral-8x7B-Instruct v0.1 7b3212fbaf88
- Replicate/Llama2-70B-Chat 02e509c78996

Note: When specifying an Ollama endpoint, available models will be requested at runtime.

Example Usage:
- Run with API keys for OpenAI and Replicate:
  cmi.py -a OpenAI:INSERT_KEY -a Replicate:INSERT_KEY
- Run with a local Ollama endpoint:
  cmi.py -a Ollama::'http://127.0.0.1:11434/api'
- Run with a local BPMN-Auto-Layout endpoint:
  cmi.py -a BPMN-Auto-Layout::'http://127.0.0.1:3000/process-diagram'

The web-based UI will be started at port <ui_port>, default: 8501
```

Example usage with Docker, BPMN-Auto-Layout and Ollama:

```sh
docker build -t fhaer/llm-cli .
docker run --rm -p 8501:8501 --pid=host -ti fhaer/llm-cmi python3 cmi.py -a Ollama::'http://172.17.0.1:11434/api' -a BPMN-Auto-Layout::'http://172.17.0.1:3000/process-diagram'
```

Example:

<img src="https://raw.githubusercontent.com/fhaer/llm-cmi/master/cmi-graphviz.png" width="100%" />

#### Related Publication

Härer, Felix (2023): Conceptual Model Interpreter for Large Language Models, accepted for: ER Forum 2023, 42nd International Conference on Conceptual Modeling (ER 2023), November 6-9, 2023, Lisbon, PT. 
