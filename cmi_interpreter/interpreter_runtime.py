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

    def __init__(self):
        print("Load Interpreter Runtime ...")

    def initialize_interpreter(self, selected_int, int_parameters):
        print("Initialize Interpreter Runtime ...")
        self.selected_interpreter = selected_int
        self.int_parameters = int_parameters

    def run_syntax(self, llm_input):

        int_input = llm_input

        #int_syntax_match = re.search(interpreter_runtime.SYNTAX_MATCH[self.selected_interpreter], source, flags=re.DOTALL)
        
        plantweb_int_engine = ""
        if self.selected_interpreter == INT_PLANTWEB_PLANTUML:
            plantweb_int_engine = "plantuml"
            # remove syntax format
            if int_input.startswith("plantuml\n"):
                int_input = int_input[9:]
            # add start and end directives
            if not '@startuml' in int_input:
                int_input = '@startuml\n' + int_input
            if not '@enduml' in int_input:
                int_input = int_input + '\n@enduml'
        elif self.selected_interpreter == INT_PLANTWEB_GRAPHVIZ:
            plantweb_int_engine = "graphviz"
            # remove syntax format
            if int_input.startswith("graphviz\n"):
                int_input = int_input[9:]
            # remove syntax format
            if int_input.startswith("dot\n"):
                int_input = int_input[4:]
            # add start and end directives
            if not '@startdot' in int_input:
                int_input = '@startdot\n' + int_input
            if not '@enddot' in int_input:
                int_input = int_input + '\n@enddot'
        elif self.selected_interpreter == INT_PLANTWEB_DITAA:
            plantweb_int_engine = "ditaa"

        print(self.int_parameters)
        plantweb_output_format = self.int_parameters['Output format']
        plantweb_use_cache = self.int_parameters['Use cache']
            
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

        if len(result) > 0:
            result_output = result[0]
        if len(result) > 1:
            result_format = result[1]

        # Decode SVG output using UTF-8
        if result_format.lower() == "svg":
            return result_output.decode('utf-8')
        
        return result_output
        