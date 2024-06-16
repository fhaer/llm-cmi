import sys
import requests
import re
import uuid

from plantweb.render import render, render_file

INT_BPMN = "BPMN-Auto-Layout"
INT_PLANTWEB = "Plantweb"

INT_BPMN_XML = INT_BPMN + "/BPMN-XML"
INT_PLANTWEB_PLANTUML = INT_PLANTWEB + "/PlantUML"
INT_PLANTWEB_GRAPHVIZ = INT_PLANTWEB + "/Graphviz"
INT_PLANTWEB_DITAA = INT_PLANTWEB + "/DITAA"

INT_BPMN_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions 
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" 
xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" 
xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" 
xmlns:di="http://www.omg.org/spec/DD/20100524/DI" 
id="<!--ID-->" 
targetNamespace="http://bpmn.io/schema/bpmn" >
<!--<bpmn:process-->
<!--<bpmndi:BPMNDiagram-->
</bpmn:definitions>
"""

INT_BPMN_TEMPLATE_REPLACE_BY_PATTERN = {
    "<bpmn:process": 
        re.compile("<(?:bpmn:)?process(.*?</(?:bpmn:)?process>)", re.DOTALL | re.IGNORECASE),
    "<bpmndi:BPMNDiagram":
        re.compile("<(?:bpmndi:)?BPMNDiagram(.*?</(?:bpmndi:)?BPMNDiagram>)", re.DOTALL | re.IGNORECASE)
}

INT_BPMN_TEMPLATE_REPLACE_BY_COMMAND = {
    "ID": '"llm-cmi-" + str(uuid.uuid4())'
}

INT_IDS = [
    INT_BPMN_XML, INT_PLANTWEB_PLANTUML, INT_PLANTWEB_GRAPHVIZ
]
INT_API_IDS = [
    INT_BPMN
]

INT_BY_ID = {
    INT_BPMN_XML : INT_BPMN,
    INT_PLANTWEB_PLANTUML : INT_PLANTWEB,
    INT_PLANTWEB_GRAPHVIZ : INT_PLANTWEB_GRAPHVIZ
}

PARAMETER_DEFAULTS = {
    INT_BPMN_XML: {
        'Output format': ['SVG']
    },
    INT_PLANTWEB_PLANTUML: {
        'Output format': ['SVG', 'PNG'],
        'Use cache': False
    },
    INT_PLANTWEB_GRAPHVIZ: {
        'Output format': ['SVG', 'PNG'],
        'Use cache': False
    },
    INT_PLANTWEB_DITAA: {
        'Output format': ['SVG', 'PNG'],
        'Use cache': False
    },
}
INT_API_ENDPOINT_DEFAULTS = {
    # Default API Endpoints (may be overwritten by commandline options)
    INT_BPMN_XML: '',
    INT_PLANTWEB_PLANTUML: '',
    INT_PLANTWEB_GRAPHVIZ: '',
    INT_PLANTWEB_DITAA: ''
}

SYNTAX_MATCH = {
    INT_BPMN_XML: r'(<bpmn(:definitions)?.*?/bpmn(:definitions)?>)',
    INT_PLANTWEB_PLANTUML: r'(.startuml.*?.enduml)',
    INT_PLANTWEB_GRAPHVIZ: r'(d?i?\S?graph\s[\w+]\s*\{.*\}).*?$',
    INT_PLANTWEB_DITAA: r'```(.*?)```'
}

SYNTAX_MATCH_CODE_BLOCK = {
    INT_BPMN_XML: r'```(.*?)```', #'@startuml(.*?)@enduml',
    INT_PLANTWEB_PLANTUML: r'```(.*?)```', #'@startuml(.*?)@enduml',
    INT_PLANTWEB_GRAPHVIZ: r'```(.*?)```', #r'(strict)? (di.?)?graph.*?\{.*\}',
    INT_PLANTWEB_DITAA: r'```(.*?)```'
}

SYNTAX_MATCH_CODE_WORD= r'`(.*?)`'

class InterpreterRuntime:
    """Runs a supported interpreter based on the output of a LLM and returns a rendering of the result"""

    def __init__(self):
        print("Load Interpreter Runtime ...")

    def initialize_interpreter(self, selected_int, int_parameters, api_key, api_endpoint):
        """Sets interpreter parameters"""

        print("Initialize Interpreter Runtime ...")
        self.selected_interpreter = selected_int
        self.int_parameters = int_parameters

        # Set API endpoint
        self.api_endpoint = ""
        if selected_int in INT_API_ENDPOINT_DEFAULTS.keys():
            self.api_endpoint = INT_API_ENDPOINT_DEFAULTS[selected_int]
        if api_endpoint:
            self.api_endpoint = api_endpoint

    def execute_plantweb(self, int_input, plantweb_int_engine, plantweb_output_format, plantweb_use_cache):
        """Run Plantweb interpreter with the given API"""

        print("Interpreter Input:\n", int_input[:20], "...", sep="")
        #print(self.int_parameters)

        result = render(
            int_input,
            engine=plantweb_int_engine,
            format=self.int_parameters['Output format'].lower(),
            cacheopts= {
                'use_cache': self.int_parameters['Use cache']
            }
        )
        return result
    
    def apply_format_plantweb(self, int_input):
        """Check interpreter input, apply the format to the input and detect language"""

        # remove syntax formatting instruction placed by LLM
        if int_input.startswith("plantuml"):
            int_input = int_input[8:]
        if int_input.startswith("graphviz"):
            int_input = int_input[8:]
        if int_input.startswith("dot"):
            int_input = int_input[3:]
        while int_input.startswith("\n"):
            int_input = int_input[1:]

        # detect UML, Graphviz or DITAA
        plantweb_int_engine = ""

        if self.selected_interpreter == INT_PLANTWEB_PLANTUML:
            plantweb_int_engine = "plantuml"
            # add start and end directives
            if not '@startuml' in int_input:
                int_input = '@startuml\n' + int_input
            if not '@enduml' in int_input:
                int_input = int_input + '\n@enduml'

        elif self.selected_interpreter == INT_PLANTWEB_GRAPHVIZ:
            plantweb_int_engine = "graphviz"
            # add start and end directives
            if not '@startdot' in int_input:
                int_input = '@startdot\n' + int_input
            if not '@enddot' in int_input:
                int_input = int_input + '\n@enddot'

        elif self.selected_interpreter == INT_PLANTWEB_DITAA:
            plantweb_int_engine = "ditaa"

        return (plantweb_int_engine, int_input)

    def apply_format_bpmn(self, int_input):
        """Check interpreter input, apply XML and BPMN XML formatting"""

        # remove code highlighting instruction generated by some LLMs
        if int_input.startswith("xml"):
            int_input = int_input[3:]
        while int_input.startswith("\n"):
            int_input = int_input[1:]

        # create template
        document = INT_BPMN_TEMPLATE
        
        # for replacements, find corresponding interpreter input and insert it
        for replacement in INT_BPMN_TEMPLATE_REPLACE_BY_PATTERN.keys():
            pattern = INT_BPMN_TEMPLATE_REPLACE_BY_PATTERN[replacement]
            match = pattern.search(int_input)
            if match:
                print("Found pattern for replacement", replacement, ", applying template ...")
                placeholder = "<!--" + replacement + "-->"
                replace_by = replacement + match.group(1)
                document = document.replace(placeholder, replace_by)

        for replacement in INT_BPMN_TEMPLATE_REPLACE_BY_COMMAND.keys():
            cmd = INT_BPMN_TEMPLATE_REPLACE_BY_COMMAND[replacement]
            placeholder = "<!--" + replacement + "-->"
            replace_by = str(eval(cmd))
            document = document.replace(placeholder, replace_by)

        return document

    def execute_bpmn(self, int_input):
        """Run BPMN interpreter"""

        print("Interpreter Input:\n", int_input[:20], " ...", sep="")

        result = None

        if self.api_endpoint:
            #auth=('apikey', self.apikey)
            data = int_input.encode('utf-8')
            headers = {'Content-Type': 'text/plain'}
            print(f"Sending request to {self.api_endpoint} ...")
            response = requests.post(self.api_endpoint, data=data, headers=headers)

            # https://github.com/MaxVidgof/bpmn-auto-layout
            # Example:
            # - curl -H "Content-Type: text/plain" --data "@test.bpmn" http://127.0.0.1:3000/process-diagram
            # - response contians JSON data: with keys layoutedDiagramXML and svg

            response_data = ""
            try:
                response_data = response.json()
                response_str = str(response_data)
                print("Response:\n", response_str[:20], "...")

                if 'svg' in response_data.keys():
                    result = [ response_data['svg'], "svg" ]
                #if 'layoutedDiagramXML' in response_data.keys():
                #    result = [ response_data['layoutedDiagramXML'], "svg" ]
            except requests.exceptions.JSONDecodeError:
                print("JSONDecodeError")
                result = [ "", "" ]

        return result


    def run_syntax(self, int_input):
        """Executes the interpreter with the provided concrete syntax"""

        result = []

        if self.selected_interpreter.startswith(INT_PLANTWEB):
            (int_engine, int_input) = self.apply_format_plantweb(int_input)
            result = self.execute_plantweb(int_input, int_engine)

        elif self.selected_interpreter.startswith(INT_BPMN):
            int_input = self.apply_format_bpmn(int_input)
            result = self.execute_bpmn(int_input)

        result_output = None
        result_format = None

        # Result output in text or image formats
        if result and len(result) > 0:
            result_output = result[0]
        if result and len(result) > 1:
            result_format = result[1]

        # Decode SVG output using UTF-8
        if result_format and result_format.lower() == "svg":
            if result_output and not isinstance(result_output, str):
                return result_output.decode('utf-8')

        return (int_input, result_output)

