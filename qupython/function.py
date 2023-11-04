import qiskit
from qiskit_aer.primitives import Sampler
from .qubit import QubitPromise, quPythonInstruction, quPythonMeasurement
from .construction import _get_promises, _construct_circuit

class quPythonFunction:
    def __init__(self, function):
        self.function = function

    def __call__(self, *args, **kwargs):
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
        self.sampler_result = Sampler().run(self.circuit).result()
        return self.interpret_result(self.sampler_result)

    def interpret_result(self, result):
        integer = [*result.quasi_dists[0]][0]  # get key from dict
        for promise in self.promises:
            promise.value = bool((1 << promise.index) & integer)
        return self.output
