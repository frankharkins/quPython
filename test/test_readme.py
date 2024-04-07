import unittest
from pathlib import Path
from textwrap import dedent
from qupython import Qubit, quantum
import qiskit
from qiskit_aer.primitives import Sampler

README_PATH = Path(__file__).parent.parent / Path("README.md")

class TestReadmeInSync(unittest.TestCase):
    """
    Make sure these code examples appear in README.md
    """
    def test_readme_in_sync(self):
        with open(__file__, "r") as f:
            source_code = f.read()
        delimiter = "# === {} code example ==="
        snippets = [
            dedent(snippet.split(delimiter.format("End"))[0])
            for snippet in source_code.split(delimiter.format("Begin"))[1:]
        ]
        with open(README_PATH) as f:
            readme = f.read()
        for snippet in snippets:
            self.assertIn(
                snippet,
                readme
            )


class TestReadmeExamples(unittest.TestCase):
    def test_all_examples(self):

        # === Begin code example ===
        from qupython import Qubit, quantum

        @quantum
        def random_bit():
            qubit = Qubit()         # Allocate new qubit
            qubit.h()               # Mutate qubit
            return qubit.measure()  # Measure qubit to bool
        # === End code example ===

        function_output = random_bit()
        self.assertTrue(
            function_output == True or function_output == False
        )


        # === Begin code example ===
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
        # === End code example ===

        # === Begin code example ===
        @quantum
        def logical_qubit_demo() -> BitPromise:
            q = LogicalQubit()
            return q.measure()
        # === End code example ===

        for _ in range(15):
            self.assertFalse(
                logical_qubit_demo()
            )

        # === Begin code example ===
        # Compile using quPython
        logical_qubit_demo.compile()

        # Draw compiled Qiskit circuit
        logical_qubit_demo.circuit.draw()
        # === End code example ===

        self.assertIsInstance(
            logical_qubit_demo.circuit,
            qiskit.QuantumCircuit
        )

        # === Begin code example ===
        from qiskit_aer.primitives import Sampler
        qiskit_result = Sampler().run(logical_qubit_demo.circuit).result()
        logical_qubit_demo.interpret_result(qiskit_result)  # returns `False`
        # === End code example ===

        self.assertFalse(
            logical_qubit_demo.interpret_result(qiskit_result)
        )
