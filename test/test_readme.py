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
        # === End code example ===

        for _ in range(10):
            result = ghz(10)
            self.assertTrue(
                all(result) or all(not r for r in result)
            )

        # === Begin code example ===
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
        # === End code example ===

        for _ in range(15):
            self.assertFalse(
                teleportation_demo()
            )

        # === Begin code example ===
        # Compile using quPython
        teleportation_demo.compile()

        # Draw compiled Qiskit circuit
        teleportation_demo.circuit.draw()
        # === End code example ===

        self.assertIsInstance(
            teleportation_demo.circuit,
            qiskit.QuantumCircuit
        )

        # === Begin code example ===
        from qiskit_aer.primitives import Sampler
        qiskit_result = Sampler().run(teleportation_demo.circuit).result()
        teleportation_demo.interpret_result(qiskit_result)  # returns `False`
        # === End code example ===

        self.assertFalse(
            teleportation_demo.interpret_result(qiskit_result)
        )
