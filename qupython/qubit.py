import qiskit.circuit.library as clib

class QubitPromiseNotResolvedError(Exception):
    pass

class QubitPromise:
    def __init__(self, measurement_instruction):
        self.measurement_instruction = measurement_instruction
        self.value = None

    def __bool__(self):
        if self.value is None:
            raise QubitPromiseNotResolvedError("This qubit promise has not been resolved yet.")
        return self.value

    def __eq__(self, other):
        if self.value is None:
            return id(self) == id(other)
        return self.value == other

    def __hash__(self):
        return id(self)

    def __repr__(self):
        if self.value is None:
            return f"QubitPromise({self.measurement_instruction})"
        return repr(self.value)

class quPythonInstruction:
    def __init__(self, qiskit_instruction, qubits):
        self.qiskit_instruction = qiskit_instruction
        self.qubits = qubits
    def __repr__(self):
        return f"quPythonInstruction({self.qiskit_instruction.name}, {self.qubits})"

class quPythonMeasurement():
    def __init__(self, qubit):
        self.promise = QubitPromise(self)
        self.qubit = qubit

class Qubit:
    def __init__(self, name=None):
        self.name = name
        self.operations = []

        self._create_1q_gate_methods()

    def __bool__(self):
        raise ValueError("Qubit can't be cast to Python bool; to measure this"
                         " Qubit, use `.measure()`")

    def _separate_conditions(self, conditions):
        # TODO: unit test
        qubits = [ c for c in conditions if isinstance(c, Qubit) ]
        promises = [ c for c in conditions if isinstance(c, QubitPromise) ]
        rest = [ c for c in conditions if not isinstance(c, (Qubit, QubitPromise)) ]
        return qubits, promises, rest

    def _create_1q_gate_methods(self):
        """
        Generate methods such as self.h, self.p, etc.
        """
        # TODO: unit test
        # TODO: neaten up
        def _create_method(gate):
            def add_gate(*args, **kwargs):
                conditions = kwargs.pop("conditions", [])
                qubits, promises, rest = self._separate_conditions(conditions) 
                if not all(rest):
                    return
                if promises:
                    raise NotImplementedError("Can't condition on a qubit measurement yet.")
                qiskit_inst = gate(*args, **kwargs)
                if qubits:
                    qiskit_inst = qiskit_inst.control(len(qubits))
                inst = quPythonInstruction(
                           qiskit_instruction=qiskit_inst,
                           qubits=qubits+[self]
                )
                for qubit in qubits+[self]:
                    qubit.operations.append(inst)
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
        # TODO: unit test
        inst = quPythonMeasurement(self)
        self.operations.append(inst)
        return inst.promise

    def get_linked_qubits(self, already_found=set()):
        # TODO: unit test
        # TODO: neaten up
        # TODO: optimize
        linked_qubits = already_found.copy() or set([self])
        for op in self.operations:
            if isinstance(op, quPythonMeasurement):
                continue
            linked_qubits |= set(op.qubits)
        if linked_qubits == already_found:
            return linked_qubits

        new_qubits = linked_qubits.copy()
        while new_qubits:
            for qubit in linked_qubits:
                new_qubits |= qubit.get_linked_qubits(already_found=linked_qubits)
            new_qubits = new_qubits - linked_qubits
            linked_qubits |= new_qubits
        return linked_qubits


