# Functions for compiling quantum circuits from BitPromise objects

import contextlib
import qiskit
from collections.abc import Mapping, Iterable
from .qubit import Qubit, BitPromise, quPythonInstruction, quPythonMeasurement
from .err_msg import ERR_MSG


def _get_promises(obj):
    """
    Recursively search Python object for `BitPromise` objects.
    """
    # TODO: unit test
    if obj is None:
        return set()

    if isinstance(obj, (int, float, bool, str)):
        return set()

    if isinstance(obj, Qubit):
        raise ValueError(ERR_MSG["ReturnQubitFromQuantumFunction"])
    if isinstance(obj, BitPromise):
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


def _get_bits_from_promises(promises):
    """
    Find all qubits needed to fulfil all promises. This includes any qubits
    that interact with measured qubits.
    """
    initial_bits=set(promises)
    all_bits = initial_bits.copy()
    for bit in initial_bits:
        all_bits |= bit.get_linked_bits(already_found=all_bits)
    return all_bits


def _waiting_for_bits(instruction):
    """
    Check if instruction can be applied to circuit.
    """
    for bit in instruction.qubits+instruction.promises:
        if bit.operations[bit.op_pointer] != instruction:
            return True
    return False


def _add_instructions_to_circuit(circuit, qubit):
    """
    Keep adding this Qubit's instructions to the circuit until complete, or
    waiting for another bit or qubit.
    """
    for op in qubit.operations[qubit.op_pointer :]:
        if _waiting_for_bits(op):
            return
        for bit in op.qubits+op.promises:
            bit.op_pointer += 1
        if isinstance(op, quPythonMeasurement):
            for promise in op.promises:
                circuit.measure(qubit.index, promise.index)
            continue
        with contextlib.ExitStack() as stack:
            for promise in op.promises:
                stack.enter_context(
                    circuit.if_test((promise.index, int(not promise.inverse)))
                )
            circuit.append(op.qiskit_instruction, [q.index for q in op.qubits])


def _construct_circuit(promises):
    """
    Compile quantum circuit needed to fulfil BitPromise values.
    """
    # TODO: unit test
    bits = _get_bits_from_promises(promises)
    qubits = [b for b in bits if isinstance(b, Qubit)]
    promises = [p for p in bits if isinstance(p, BitPromise)]
    for index, qubit in enumerate(qubits):
        qubit.index = index  # Map qupython.Qubit to circuit qubit
        qubit.op_pointer = 0  # To keep track of compiled operations
    for index, promise in enumerate(promises):
        promise.index = index  # Map promise to circuit clbit
        promise.op_pointer = 0

    circuit = qiskit.QuantumCircuit(len(qubits), len(promises))
    while any(q.op_pointer < len(q.operations) for q in qubits):
        for qubit in qubits:
            _add_instructions_to_circuit(circuit, qubit)
    return circuit
