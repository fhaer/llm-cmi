import sys
import requests
import re

from plantweb.render import render, render_file

INT_BPMN = "BPMN-Auto-Layout"
INT_PLANTWEB = "Plantweb"

INT_BPMN_XML = INT_BPMN + "/BPMN-XML"
INT_PLANTWEB_PLANTUML = INT_PLANTWEB + "/PlantUML"
INT_PLANTWEB_GRAPHVIZ = INT_PLANTWEB + "/Graphviz"
INT_PLANTWEB_DITAA = INT_PLANTWEB + "/DITAA"

INT_IDS = [
    INT_BPMN_XML, INT_PLANTWEB_PLANTUML, INT_PLANTWEB_GRAPHVIZ
]
INT_API_IDS = [
    INT_BPMN
]

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
INT_API_ENDPOINT_DEFAULTS = {#
    # Default API Endpoints (may be overwritten by commandline options)
    INT_BPMN_XML: '',
    INT_PLANTWEB_PLANTUML: '',
    INT_PLANTWEB_GRAPHVIZ: '',
    INT_PLANTWEB_DITAA: ''
}

SYNTAX_MATCH = {
    INT_BPMN_XML: r'(<bpmn(:definitions)?.*?/bpmn(:definitions)?>)',
    INT_PLANTWEB_PLANTUML: r'@startuml(.*?)@enduml',
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

        print("Interpreter Input:\n", int_input, sep="")
        #print(self.int_parameters)
        result = render(
            int_input,
            engine=plantweb_int_engine,
            format=plantweb_output_format.lower(),
            cacheopts= {
                'use_cache': plantweb_use_cache
            }
        )
        return result

    def execute_bpmn(self, int_input):
        """Run BPMN interpreter"""

        print("Interpreter Input:\n", int_input, sep="")

        result = None

        if self.api_endpoint:
            #auth=('apikey', self.apikey)
            data = int_input.encode('utf-8')
            headers = {'Content-Type': 'text/plain'}
            response = requests.post(self.api_endpoint, data=data, headers=headers)

            # https://github.com/MaxVidgof/bpmn-auto-layout
            # Example:
            # - curl -H "Content-Type: text/plain" --data "@test.bpmn" http://127.0.0.1:3000/process-diagram
            # - response contians JSON data: with keys layoutedDiagramXML and svg

            response_data = ""
            try:
                print(response.json())
                response_data = response.json()

                if 'svg' in response_data.keys():
                    result = [ response_data['svg'], "svg" ]
                #if 'layoutedDiagramXML' in response_data.keys():
                #    result = [ response_data['layoutedDiagramXML'], "svg" ]
            except requests.exceptions.JSONDecodeError:
                print("JSONDecodeError")
                result = [ "", "" ]

        return result


    def run_syntax(self, input_syntax):
        """Executes the interpreter with the provided concrete syntax"""

        int_input = input_syntax

        # remove syntax format
        if int_input.startswith("plantuml\n"):
            int_input = int_input[9:]
        if int_input.startswith("graphviz\n"):
            int_input = int_input[9:]
        if int_input.startswith("dot\n"):
            int_input = int_input[4:]

        # set the engine, add interpreter directives and execute interpreter
        result = []

        if self.selected_interpreter.startswith(INT_PLANTWEB):

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
            
            plantweb_output_format = self.int_parameters['Output format']
            plantweb_use_cache = self.int_parameters['Use cache']

            # Execute interpreter
            result = self.execute_plantweb(int_input, plantweb_int_engine, plantweb_output_format, plantweb_use_cache)

        elif self.selected_interpreter.startswith(INT_BPMN) and not re.search("<\?xml", int_input):
            # add prolog
            int_input = '<?xml version="1.0" encoding="UTF-8"?>' + int_input

            # Execute interpreter
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
        
        return result_output
        
