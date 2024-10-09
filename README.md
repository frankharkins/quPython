# quPython

> Quantum programs that read like Python

Stop writing code that looks like assembly! quPython makes quantum programs as
easy as regular Python code. To illustrate, here's "Hello, world!" in quPython
(make sure to `pip install qupython` first):

```python
from qupython import Qubit, quantum

@quantum
def random_bit():
    qubit = Qubit()         # Allocate new qubit
    qubit.h()               # Mutate qubit
    return qubit.measure()  # Measure qubit to bool

print(random_bit())         # Prints "True" or "False"
```

The `@quantum` decorator converts the function into a quantum function that can
be executed on a quantum computer. When you run `random_bit`, quPython compiles
your function to a quantum program, executes it, and returns the results. Read
on to see why this is a big deal.

## Use Python to organise your quantum programs

quPython just a wrapper for Qiskit, but it makes two different design decisions:
1. Quantum programs are (decorated) Python functions, no separate circuit objects.
2. Quantum operations are methods on the `Qubit` class.

These small changes make a big difference in how you write your programs.
Qubits feel like standard Python objects, which makes it natural to organise
quantum programs using classes and other Python features. The following example
creates a simple logical qubit class. This shows some nice consequences of
quPython's design decisions:

* The lower level qubits and operation are handled by the class
* Qubits and classical bits can be initialized in methods and scoped to those methods
* Methods return classical bit objects to be used in the program or returned to
  the user; no need to keep track of bit indices or registers.

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
        # Note the `out` qubit is scoped to this function
        out = Qubit().h()
        for q in self.qubits:
            with out.as_control():
                q.z()
        return out.h().measure()
```

Here's how you'd use this class.

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

See the [Logical qubit
example](https://github.com/frankharkins/quPython/blob/main/examples/logical-qubit.md)
for a more complete class.

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

You can compile the function without executing it, optimize the circuit,
execute it however you like, then use quPython to interpret the results.

```python
from qiskit_aer.primitives import Sampler
qiskit_result = Sampler().run(logical_qubit_demo.circuit).result()
logical_qubit_demo.interpret_result(qiskit_result)  # returns `False`
```
