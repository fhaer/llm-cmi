import sys
import requests

from plantweb.render import render, render_file

INT_PLANTWEB = "Plantweb"

INT_PLANTWEB_PLANTUML = INT_PLANTWEB + "/PlantUML"
INT_PLANTWEB_GRAPHVIZ = INT_PLANTWEB + "/Graphviz"
INT_PLANTWEB_DITAA = INT_PLANTWEB + "/DITAA"

INTERPRETER_IDS = [
    INT_PLANTWEB_PLANTUML, INT_PLANTWEB_GRAPHVIZ
]

PARAMETER_DEFAULTS = {
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

SYNTAX_MATCH = {
    INT_PLANTWEB_PLANTUML: r'```(.*?)```', #'@startuml(.*?)@enduml',
    INT_PLANTWEB_GRAPHVIZ: r'```(.*?)```', #r'(strict)? (di.?)?graph.*?\{.*\}',
    INT_PLANTWEB_DITAA: r'```(.*?)```'
}

SYNTAX_MATCH_CODE_BLOCK = r'`(.*?)`'

class InterpreterRuntime:
    """Runs a supported interpreter based on the output of a LLM and returns a rendering of the result"""

    def __init__(self):
        print("Load Interpreter Runtime ...")

    def initialize_interpreter(self, selected_int, int_parameters):
        """Sets interpreter parameters"""

        print("Initialize Interpreter Runtime ...")
        self.selected_interpreter = selected_int
        self.int_parameters = int_parameters

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

        # set the engine for the plantweb interpreter and add interpreter directives
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

        #print(self.int_parameters)
        plantweb_output_format = self.int_parameters['Output format']
        plantweb_use_cache = self.int_parameters['Use cache']
        
        # Execute interpreter
        result = render(
            int_input,
            engine=plantweb_int_engine,
            format=plantweb_output_format.lower(),
            cacheopts= {
                'use_cache': plantweb_use_cache
            }
        )

        result_output = None
        result_format = None

        # Result output in text or image formats
        if len(result) > 0:
            result_output = result[0]
        if len(result) > 1:
            result_format = result[1]

        # Decode SVG output using UTF-8
        if result_format.lower() == "svg":
            return result_output.decode('utf-8')
        
        return result_output
        