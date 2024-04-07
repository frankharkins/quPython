from qupython import Qubit, quantum
import unittest

class GHZState(unittest.TestCase):
    def test(self):
        @quantum
        def ghz(num_bits: int):
            """
            Create and measure a GHZ state
            """
            qubits = [ Qubit() for _ in range(num_bits) ]
            control, targets = qubits[0], qubits[1:]
            control.h()
            for target in targets:
                with control.as_control():
                    target.x()
            return [ qubit.measure() for qubit in qubits ]

        for _ in range(10):
            result = ghz(10)
            self.assertTrue(
                all(result) or all(not r for r in result)
            )

class CustomDataTypes(unittest.TestCase):
    def test(self):
        class QuIntPromise:
            def __init__(self, bits):
                self.bits = bits
                self.value = None
            def __int__(self):
                return sum(1<<i for i, b in enumerate(self.bits) if b)
            def __repr__(self):
                return str(int(self))

        class QuInt:
            def __init__(self, value, n_bits):
                self._qubits = [ Qubit() for _ in range(n_bits) ]
                for i, qubit in enumerate(self._qubits):
                    if (1<<i) & value:
                        qubit.x()
            def __iadd__(self, other):
                for _ in range(other):
                    for index, target in enumerate(reversed(self._qubits)):
                        target.x(conditions=self._qubits[:-index-1])
                return self
            def measure(self):
                return QuIntPromise([q.measure() for q in self._qubits])

        @quantum
        def test_int():
            i = QuInt(value=5, n_bits=5)
            i += 2
            return i.measure()

        self.assertEqual(
            repr(test_int()),
            "7"
        )
