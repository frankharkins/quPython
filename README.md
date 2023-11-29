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

Create classes for quantum data just as you would conventional data, and
condition quantum gates on classical and quantum data in exactly the same way.

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

## Generate Qiskit circuits

If you want, you can just use quPython to create Qiskit circuits with Pythonic
syntax (rather than the assembly-like syntax of `qc.cx(0, 1)` in native
Qiskit).

```python
# Compile using quPython
teleportation_demo.compile()

# Draw compiled Qiskit circuit
teleportation_demo.circuit.draw()
```

```
                    ┌───┐┌─┐                           
q_0: ────────────■──┤ H ├┤M├───────────────────────────
          ┌───┐  │  └───┘└╥┘┌──────────┐┌──────────┐┌─┐
q_1: ─────┤ X ├──┼────────╫─┤0         ├┤0         ├┤M├
     ┌───┐└─┬─┘┌─┴─┐ ┌─┐  ║ │          ││          │└╥┘
q_2: ┤ H ├──■──┤ X ├─┤M├──╫─┤          ├┤          ├─╫─
     └───┘     └───┘ └╥┘  ║ │  If_else ││          │ ║ 
c_0: ═════════════════╬═══╬═╡          ╞╡  If_else ╞═╩═
                      ║   ║ │          ││          │   
c_1: ═════════════════╩═══╬═╡0         ╞╡          ╞═══
                          ║ └──────────┘│          │   
c_2: ═════════════════════╩═════════════╡0         ╞═══
                                        └──────────┘   
```

You can compile the function without executing it, optimize the cirucit,
execute it however you like, then use quPython to interpret the results.

```python
from qiskit_aer.primitives import Sampler
qiskit_result = Sampler().run(teleportation_demo.circuit).result()
teleportation_demo.interpret_result(qiskit_result)  # returns `False`
```
