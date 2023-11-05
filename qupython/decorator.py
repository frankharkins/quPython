# The @quantum function decorator

from .function import quPythonFunction


def quantum(func):
    """
    Decorator for quantum functions. Calling a @quantum function will compile
    and execute a quantum circuit.
    """
    return quPythonFunction(func)
