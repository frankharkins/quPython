# Class for @quantum functions

from typing import Callable

import qiskit
from qiskit_aer.primitives import Sampler
from .construction import _get_promises, _construct_circuit
from .qubit import BitPromise
from .err_msg import ERR_MSG


class quPythonFunction:
    """
    A wrapper to compile a quantum circuit from a function's outputs, execute
    it, and resolve any `BitPromise` objects. You'll probably create these
    objects through through the `@quantum` decorator.

    ```python
    from qupython import Qubit, quantum

    @quantum
    def my_function():
        return Qubit().measure()

    type(my_function)  # qupython.function.quPythonFunction
    ```

    Calling an instance of this class will (in the following order):
    1. Run the function in the Python interpreter
    2. Intercept the output of the function and search for any `BitPromise` objects.
    3. Compile the Qiskit circuit needed to calculate the `BitPromise` objects.
    4. Execute the circuit on a quantum backend.
    5. Use the execution results to assign the `BitPromise.value` attributes, resolving the promises.

    Split these steps up by calling methods on this object rather than
    calling it. The `compile` method does steps 1-3, but does not execute the
    circuit on a quantum backend. It stores the compiled
    [`qiskit.QuantumCircuit`](https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.QuantumCircuit)
    in the `circuit` attribute. 

    ```python
    my_function.compile()
    my_function.circuit.draw()
    ```

    ```output
         ┌─┐
      q: ┤M├
         └╥┘
    c: 1/═╩═
          0
    ```

    The `run` method carries out steps 4-5 using the circuit from the `circuit`
    attribute. If you replace the attribute with a different circuit (such as
    an optimized circuit), it will use that.

    ```python
    my_function.run()  # BitPromise with value False
    ```

    The `interpret_result` method uses a `SamplerResult` of the compiled
    circuit to resolve `BitPromises` and return the function output. Use this
    if you want to control the circuit execution.

    ```python
    from qiskit_aer.primitives import Sampler
    qiskit_result = Sampler().run(my_function.circuit).result()
    my_function.interpret_result(qiskit_result)  # BitPromise with value False
    ```

    """
    def __init__(self, function: Callable):
        self.function: Callable = function
        """
        The function to be compiled. It should return `BitPromise` objects.
        """
        self.circuit: qiskit.QuantumCircuit | None = None
        """
        The compiled Qiskit circuit. This is `None` until the class is
        called or `compile` is run.
        """
        self.promises: list[BitPromise] = None
        """The `BitPromise` objects to be resolved"""

    def __call__(self, *args, **kwargs):
        """
        Run the function, compile the circuit, execute the circuit, and return
        the results.
        """
        self.compile(*args, **kwargs)
        return self.run()

    def compile(self, *args, **kwargs):
        """
        Run function (with args and keyword args), collect promises, and
        compile circuit, but don't execute the circuit. Stores the compiled
        circuit in the `circuit` attribute.
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

    def interpret_result(self, result: qiskit.primitives.SamplerResult):
        """
        Given a one-shot `SamplerResult`, parse the result and return the
        function's output with resolved promises.
        """
        if result is None and self.promises == []:
            # Function is not quantum
            return self.output

        integer = [*result.quasi_dists[0]][0]  # Get 0th key from dict
        for promise in self.promises:
            promise.value = bool((1 << promise.index) & integer)
        return self.output

class quPythonFunctionError(Exception):
    pass
