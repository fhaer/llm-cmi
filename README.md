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
- BPMN-Auto-Layout

Supported LLMs:
- OpenAI/gpt-4o-2024-05-13
- OpenAI/gpt-4-turbo-2024-04-09
- OpenAI/gpt-4-0125-preview
- OpenAI/gpt-4-0613
- OpenAI/gpt-3.5-turbo-0125
- Replicate/Mixtral-8x7B-Instruct v0.1 7b3212fbaf88
- Replicate/Llama2-70B-Chat
- Replicate/Llama3-70B-Chat
- Ollama models (loaded at runtime)

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
docker run --rm -p 8501:8501 --pid=host -ti -v $PWD/cmi_logs:/app/cmi_logs fhaer/llm-cmi python3 cmi.py -a Ollama::'http://172.17.0.1:11434/api' -a BPMN-Auto-Layout::'http://172.17.0.1:3000/process-diagram'
```

Example:

<img src="https://raw.githubusercontent.com/fhaer/llm-cmi/master/cmi-graphviz.png" width="100%" />

#### Related Publication

Härer, Felix (2023): Conceptual Model Interpreter for Large Language Models, accepted for: ER Forum 2023, 42nd International Conference on Conceptual Modeling (ER 2023), November 6-9, 2023, Lisbon, PT. 
