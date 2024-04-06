# Class for @quantum functions

import qiskit
from qiskit_aer.primitives import Sampler
from .qubit import quPythonInstruction, quPythonMeasurement
from .construction import _get_promises, _construct_circuit
from .err_msg import ERR_MSG


class quPythonFunctionError(Exception):
    pass


class quPythonFunction:
    """
    These functions include a quantum part that can be compiled into a quantum
    cirucit. Calling this object runs the function, executes the circuit, and
    inserts the results into your returned object.
    """

    def __init__(self, function):
        self.function = function
        self.circuit = None
        self.promises = None

    def __call__(self, *args, **kwargs):
        """
        Run the function, compile the circuit, execute the circuit, and return
        the results.
        """
        self.compile(*args, **kwargs)
        return self.run()

    def compile(self, *args, **kwargs):
        """
        Run function, collect promises, and compile circuit, but don't execute
        the circuit.
        """
        self.output = self.function(*args, **kwargs)
        self.promises = list(_get_promises(self.output))
        self.circuit = _construct_circuit(self.promises)

    def run(self):
        """
        Run the pre-compiled circuit, interpret the result, and return the
        output object with fulfilled promises.
        """
        if self.promises is None:
            raise quPythonFunctionError(ERR_MSG["CompileFunctionBeforeRunning"])
        if self.promises == []:
            return self.output
        self.sampler_result = Sampler().run(self.circuit).result()
        return self.interpret_result(self.sampler_result)

    def interpret_result(self, result):
        """
        Given a one-shot SamplerResult, this method parses the result and
        returns the function output with fulfilled promises.
        """
        if result is None and self.promises == []:
            # Function is not quantum
            return self.output

        integer = [*result.quasi_dists[0]][0]  # Get 0th key from dict
        for promise in self.promises:
            promise.value = bool((1 << promise.index) & integer)
        return self.output
