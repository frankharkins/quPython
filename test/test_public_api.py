from qupython import Qubit, quantum
import unittest

class Compilation(unittest.TestCase):
    def test_simple_example(self):
        @quantum
        def ghz(n):
            qubits = [ Qubit() for _ in range(n) ]
            qubits[0].h()
            for target in qubits[1:]:
                target.x(conditions=[qubits[0]])
            return qubits[0].measure()

        for n in [1, 5, 20]:
            ghz.compile(n)
            qc = ghz.circuit
            self.assertEqual(qc.num_qubits, n)
            self.assertEqual(qc.data[0].operation.name, 'h')

    def test_another_simple_example(self):
        def swap(q0: Qubit, q1: Qubit):
            q0.x(conditions=[q1])
            q1.x(conditions=[q0])
            q0.x(conditions=[q1])

        class CustomClass:
            def __init__(self, qubits):
                self.qubits = qubits

        @quantum
        def lotsa_swaps(n):
            qubits = [ Qubit() for _ in range(n) ]
            for i in range(n//2):
                swap(qubits[i], qubits[-(i+1)])
            return CustomClass([ qubit.measure() for qubit in qubits ])

        for n in [3, 9, 21, 49]:
            lotsa_swaps.compile(n)
            qc = lotsa_swaps.circuit
            self.assertEqual(qc.num_qubits, n)
            self.assertEqual(
                    len(qc.data),
                    n + 3*(n//2)
            )

class QuantumFunctionCallable(unittest.TestCase):
    def test_ordering(self):
        @quantum
        def get_bits():
            qubits = [ Qubit() for _ in range(10) ]
            qubits[0].x()
            return [ qubit.measure() for qubit in qubits ]

        for _ in range(20):
            self.assertEqual(get_bits()[0], True)
