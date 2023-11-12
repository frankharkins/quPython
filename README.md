# quPython

> Quantum programs directly in Python.

quPython compiles Python functions into quantum programs, executes the
programs, and returns the results as standard Python data types.

## What can it do?

Initialize a `quPython.Qubit` object just like any other object and use it
inside a `@quantum` function.

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

quPython makes writing quantum programs feel like any other Python program.

### Code examples

Get a feel for quPython with code examples for popular quantum circuits.

```python
@quantum
def ghz(num_bits: int):
    """
    Create and measure a GHZ state
    """
    qubits = [ Qubit() for _ in range(num_bits) ]
    control, targets = qubits[0], qubits[1:]
    control.h()
    for target in targets:
        target.x(conditions=[control])
    return [ qubit.measure() for qubit in qubits ]
```

```python
import math

@quantum
def qft(num_qubits: int):
    qubits = [ Qubit() for _ in range(num_qubits) ]
    def rotate(qubits):
        """One iteration of the QFT rotations"""
        qubits[0].h()
        for index, control in enumerate(qubits[1:]):
            power = index + 1
            qubits[0].p(
                math.pi/2**power,
                conditions=[control]
            )

    for index in range(len(qubits)):
        rotate(qubits[index:])
    return [q.measure() for q in qubits[::-1]]
```

```python
class BellPair:
    def __init__(self):
        self.left = Qubit().h()
        self.right = Qubit().x(conditions=[self.left])

@quantum
def teleportation_demo():
    message = Qubit()

    bell_pair = BellPair()
    do_x = bell_pair.left.x(conditions=[message]).measure()
    do_z = message.h().measure()

    bell_pair.right.x(conditions=[do_x]).z(conditions=[do_z])
    return bell_pair.right.measure()
```

### Generate Qiskit circuits

If you want, you can just use quPython to create Qiskit circuits with Pythonic
syntax (rather than the assembly-like syntax of `qc.cx(0, 1)` in native
Qiskit).

```python
# Compile using quPython
random_bit.compile()

# Execute using Qiskit
qiskit_circuit = random_bit.circuit
```

If you want more control over the quantum program, you can compile the function
without executing it, optimize and execute it however you like, then use
quPython to interpret the results.

```python
from qiskit.primitives import Sampler
qiskit_result = Sampler().run(qiskit_circuit).result()
function_output = random_bit.interpret_result(qiskit_result)
```

## How it works

> For contributors (or the curious)

To see how quPython works, we'll use the `Qubit` object outside a `@quantum`
function. `Qubit` objects store a list of operations that act on them.

```python
>>> qubit = Qubit()
>>> qubit.h()
>>> qubit.operations
[quPythonInstruction(h, [<qupython.qubit.Qubit object at 0x7fddf68504d0>])]
```

The only way to get a classical data type from a quantum program is the
`Qubit.measure` method. We give the appearance that this returns a `bool`, but
it actually returns a `QubitPromise` object, which saves a link to the measure
operation that created it.

```python
>>> promise = qubit.measure()
>>> promise
QubitPromise(<qupython.qubit.quPythonMeasurement object at 0x7fddf0ddbbd0>)
```

When the user calls a `@quantum` function, quPython intercepts the output,
finds any `QubitPromise` objects, then traces back the `Qubits` those promises
came from. With this information, quPython can construct the `QuantumCircuit`
needed to fulfil the promises. quPython then executes the circuit and fills in
the `QubitPromise` values.
