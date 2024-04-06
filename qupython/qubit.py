import qiskit.circuit.library as clib
from .err_msg import ERR_MSG


class QubitPromiseNotResolvedError(Exception):
    pass

class _Bit:
    operations: list

    def get_linked_bits(self, already_found=None):
        # TODO: unit test
        searched_bits = set()
        all_known_bits = { self }
        while len(searched_bits) < len(all_known_bits):
            for bit in (all_known_bits - searched_bits):
                for op in bit.operations:
                    all_known_bits |= set(op.qubits + op.promises)
                searched_bits.add(bit)
        return all_known_bits


class QubitPromise(_Bit):
    """
    Placeholder for qubit measurement results.

    Each promise belongs to exactly one measurement instruction. At the end of
    a `@quantum` function, quPython executes the circuit needed to fulfil any
    returned promises.

    After the values are determined, a `QubitPromise` tries to behave as much
    like a `bool` as possible. Unfortunately, there are some quirks because
    `QubitPromises` need to have unique hashes before circuit compilation, but
    `bool`s all have the same hash (0 or 1) and you can't change an object's
    hash without breaking basic Python functionality. The following code
    snippet shows an example.

    ```
    # Create fulfilled qubit promise
    promise = QubitPromise(None)
    promise.value = True

    # Show unexpected behavior
    promise == True  # True
    promise in (True, False)  # False
    ```

    Currently not sure what the best behavior is. Options are:
      * Keep it like this, and encourage users to cast to `bool` ASAP
      * Keep like this, but have quPython return a new copy of the data with
        _actual_ `bool`s
      * Something else?
    """

    def __init__(self, measurement_instruction, inverse=False):
        self.operations = [measurement_instruction]
        self.inverse = inverse
        self.value = None

    def __bool__(self):
        if self.value is None:
            raise QubitPromiseNotResolvedError(ERR_MSG["QubitPromiseNotResolved"])
        return self.value

    def __int__(self):
        return int(bool(self))

    def __eq__(self, other):
        if self.value is None:
            return id(self) == id(other)
        return self.value == other

    def __hash__(self):
        return id(self)

    def __repr__(self):
        if self.value is None:
            return f"QubitPromise({self.operations})"
        return repr(self.value)

    def __invert__(self):
        # TODO: This is a bit inefficient as it adds a new measurement each
        # time we invert the promise
        measurement_instruction = self.operations[0]
        new_promise = QubitPromise(
            measurement_instruction,
            inverse= not self.inverse
        )
        measurement_instruction.promises.append(new_promise)
        return new_promise


class quPythonInstruction:
    def __init__(self, qiskit_instruction, qubits, promises=[]):
        self.qiskit_instruction = qiskit_instruction
        self.qubits = qubits
        self.promises = promises

    def __repr__(self):
        return f"quPythonInstruction({self.qiskit_instruction.name}, {self.qubits})"


class quPythonMeasurement:
    def __init__(self, qubit):
        self.promises = [QubitPromise(self)]
        self.qubits = [qubit]


class Qubit(_Bit):
    def __init__(self, name=None):
        self.name = name
        self.operations = []

        self._create_1q_gate_methods()

    def __bool__(self):
        raise ValueError(
            "Can't cast Qubit to bool; use `.measure()` to measure"
            " the qubit instead."
        )

    def _separate_conditions(self, conditions):
        qubits = [c for c in conditions if isinstance(c, Qubit)]
        promises = [c for c in conditions if isinstance(c, QubitPromise)]
        build_time_conditions = [c for c in conditions if not isinstance(c, (Qubit, QubitPromise))]
        return qubits, promises, build_time_conditions

    def _create_1q_gate_methods(self):
        """
        Generate methods such as self.h, self.p, etc.
        This method runs on object initialization.
        """

        # TODO: unit test
        # TODO: neaten up
        def _create_method(gate):
            def add_gate(*args, **kwargs):
                conditions = kwargs.pop("conditions", [])
                qubits, promises, build_time_conditions = self._separate_conditions(conditions)
                if not all(build_time_conditions):
                    return
                qiskit_inst = gate(*args, **kwargs)
                if qubits:
                    qiskit_inst = qiskit_inst.control(len(qubits))
                inst = quPythonInstruction(
                    qiskit_instruction=qiskit_inst,
                    qubits=qubits + [self],
                    promises=promises
                )
                for qubit in qubits + [self]:
                    qubit.operations.append(inst)
                for promise in promises:
                    promise.operations.append(inst)
                return self

            return add_gate

        for gate, name in [
            (clib.XGate, "x"),
            (clib.YGate, "y"),
            (clib.ZGate, "z"),
            (clib.HGate, "h"),
            (clib.SGate, "s"),
            (clib.SdgGate, "sdg"),
            (clib.TGate, "t"),
            (clib.TdgGate, "tdg"),
            (clib.PhaseGate, "p"),
            (clib.RXGate, "rx"),
            (clib.RYGate, "ry"),
            (clib.RZGate, "rz"),
            (clib.UGate, "u"),
        ]:
            setattr(self, name, _create_method(gate))

    def measure(self):
        """
        Add measure instruction to Qubit and return QubitPromise
        """
        inst = quPythonMeasurement(self)
        self.operations.append(inst)
        return inst.promises[0]
