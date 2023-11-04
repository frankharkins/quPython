import qiskit
from .qubit import QubitPromise, quPythonInstruction, quPythonMeasurement
from .construction import _get_promises, _construct_circuit

class quPythonFunction:
    def __init__(self, function):
        self.function = function

    def __call__(self, *args, **kwargs):
        self.compile(*args, **kwargs)
        return output

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
        _set_promise_values(self.sampler_result, self.promises)
        return self.output
