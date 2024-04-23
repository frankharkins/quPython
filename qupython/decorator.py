# The @quantum function decorator

from .function import quPythonFunction


def quantum(func) -> quPythonFunction:
    """
    Decorator for quantum functions. Calling a `@quantum` function will compile
    and execute a quantum circuit.

    ```python
    from qupython import Qubit, quantum

    @quantum
    def bell_example():
        left, right Qubit(), Qubit()
        with left.as_control():
            right.x()
        return left.measure(), right.measure()

    my_function()  # Returns either (True, True) or (False, False)
    ```

    See qupython.function.quPythonFunction for more information.
    """
    return quPythonFunction(func)
