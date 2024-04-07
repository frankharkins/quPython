# quPython

```
pip install qupython
```

quPython compiles Python functions into quantum programs, executes the
programs, and returns the results as `bool`-like objects.

Initialize a `quPython.Qubit` object just like any other object and use it
inside a `@quantum` function. These are the only two imports you'll need.

```python
from qupython import Qubit, quantum

@quantum
def random_bit():
    qubit = Qubit()         # Allocate new qubit
    qubit.h()               # Mutate qubit
    return qubit.measure()  # Measure qubit to bool
```

When you run `random_bit`, quPython compiles your function to a quantum
program, executes it, and returns results.

```python
>>> random_bit()
True
```

## Python-like data management

Create classes for quantum data just as you would conventional data. The
following example creates a simple logical qubit class. See the [Logical qubit
example](./examples/logical-qubit.md) for a more complete class.

```python
from qupython import Qubit, quantum
from qupython.typing import BitPromise

class LogicalQubit:
    """
    Simple logical qubit using the five-qubit code.
    See https://en.wikipedia.org/wiki/Five-qubit_error_correcting_code
    """
    def __init__(self):
        """
        Create new logical qubit and initialize to logical |0>.
        Uses initialization procedure from https://quantumcomputing.stackexchange.com/a/14449
        """
        self.qubits = [Qubit() for _ in range(5)]
        self.qubits[4].z()
        for q in self.qubits[:4]:
            q.h()
            with q.as_control():
                self.qubits[4].x()
        for a, b in [(0,4),(0,1),(2,3),(1,2),(3,4)]:
            with self.qubits[b].as_control():
                self.qubits[a].z()

    def measure(self) -> BitPromise:
        """
        Measure logical qubit to single classical bit
        """
        out = Qubit().h()
        for q in self.qubits:
            with out.as_control():
                q.z()
        return out.h().measure()
```

This abstracts the bit-level operations away from the user.

```python
@quantum
def logical_qubit_demo() -> BitPromise:
    q = LogicalQubit()
    return q.measure()
```

```python
>>> logical_qubit_demo()
False
```

## Generate Qiskit circuits

If you want, you can just use quPython to create Qiskit circuits with Pythonic
syntax (rather than the assembly-like syntax of `qc.cx(0, 1)` in native
Qiskit).

```python
# Compile using quPython
logical_qubit_demo.compile()

# Draw compiled Qiskit circuit
logical_qubit_demo.circuit.draw()
```

```
     ┌───┐                                                       
q_0: ┤ H ├────────────■────────■───────────■─────■───────────────
     ├───┤            │        │           │     │               
q_1: ┤ H ├──■─────────┼────────┼──■──■──■──┼─────┼───────────────
     ├───┤  │         │        │  │  │  │  │     │               
q_2: ┤ H ├──┼────■────┼────────┼──┼──■──┼──■──■──┼───────────────
     ├───┤┌─┴─┐┌─┴─┐┌─┴─┐┌───┐ │  │     │     │  │               
q_3: ┤ Z ├┤ X ├┤ X ├┤ X ├┤ X ├─┼──■──■──┼─────┼──┼─────■─────────
     ├───┤└───┘└───┘└───┘└─┬─┘ │     │  │     │  │     │ ┌───┐┌─┐
q_4: ┤ H ├─────────────────┼───┼─────┼──■─────■──■──■──■─┤ H ├┤M├
     ├───┤                 │   │     │              │    └───┘└╥┘
q_5: ┤ H ├─────────────────■───■─────■──────────────■──────────╫─
     └───┘                                                     ║ 
c: 1/══════════════════════════════════════════════════════════╩═
                                                               0 
```

You can compile the function without executing it, optimize the cirucit,
execute it however you like, then use quPython to interpret the results.

```python
from qiskit_aer.primitives import Sampler
qiskit_result = Sampler().run(logical_qubit_demo.circuit).result()
logical_qubit_demo.interpret_result(qiskit_result)  # returns `False`
```
