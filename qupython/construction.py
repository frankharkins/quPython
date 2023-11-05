# Functions for compiling quantum circuits from QubitPromise objects

import qiskit
from collections.abc import Mapping, Iterable
from .qubit import Qubit, QubitPromise, quPythonInstruction, quPythonMeasurement
from .err_msg import ERR_MSG


def _get_promises(obj):
    """
    Recursively search Python object for `QubitPromises`.
    """
    # TODO: unit test
    if obj is None:
        return set()

    if isinstance(obj, (int, float, bool, str)):
        return set()

    if isinstance(obj, Qubit):
        raise ValueError(ERR_MSG["ReturnQubitFromQuantumFunction"])
    if isinstance(obj, QubitPromise):
        return set([obj])

    if hasattr(obj, "__dict__"):
        obj = obj.__dict__

    if isinstance(obj, Mapping):
        promises = set()
        for key, value in obj.items():
            promises |= _get_promises(key)
            promises |= _get_promises(value)
        return promises

    if isinstance(obj, Iterable):
        promises = set()
        for element in obj:
            promises |= _get_promises(element)
        return promises

    raise ValueError(ERR_MSG["CantSearchObjectForPromises"].format(obj=type(obj)))


def _get_qubits_from_promises(promises):
    """
    Find all qubits needed to fulfil all promises. This includes any qubits
    that interact with measured qubits.
    """
    # TODO: unit test
    promise_qubits = [promise.measurement_instruction.qubit for promise in promises]
    all_qubits = set(promise_qubits)
    for qubit in promise_qubits:
        all_qubits |= qubit.get_linked_qubits()
    return all_qubits


def _waiting_for_qubits(instruction):
    """
    Check if instruction can be applied to circuit.
    """
    if isinstance(instruction, quPythonMeasurement):
        return False
    for qubit in instruction.qubits:
        if qubit.operations.index(instruction) != qubit.op_pointer:
            return True
    return False


def _add_instructions_to_circuit(circuit, qubit):
    """
    Keep adding this Qubit's instructions to the circuit until complete, or
    waiting for another qubit.
    """
    for op in qubit.operations[qubit.op_pointer :]:
        if _waiting_for_qubits(op):
            return
        if isinstance(op, quPythonMeasurement):
            qubit.op_pointer += 1
            circuit.measure(qubit.index, op.promise.index)
            continue
        circuit.append(op.qiskit_instruction, [q.index for q in op.qubits])
        for q in op.qubits:
            q.op_pointer += 1


def _construct_circuit(promises):
    """
    Compile quantum circuit needed to fulfil QubitPromise values.
    """
    # TODO: unit test
    qubits = _get_qubits_from_promises(promises)
    for index, qubit in enumerate(qubits):
        qubit.index = index  # Map qupython.Qubit to circuit qubit
        qubit.op_pointer = 0  # To keep track of compiled operations
    for index, promise in enumerate(promises):
        promise.index = index  # Map promise to circuit clbit

    circuit = qiskit.QuantumCircuit(len(qubits), len(promises))
    while any(q.op_pointer < len(q.operations) for q in qubits):
        for qubit in qubits:
            _add_instructions_to_circuit(circuit, qubit)
    return circuit
