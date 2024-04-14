from __future__ import annotations


from contextvars import ContextVar
from typing import Self

import qiskit.circuit.library as clib
from .err_msg import ERR_MSG

__active_controls__ = ContextVar("qupython_active_controls", default=())

class Bit:
    """
    Base class for `Qubit` and `BitPromise` objects; you shouldn't create an
    instance of this class yourself.
    """
    operations: list
    """History of operations on the bit"""

    def _get_linked_bits(self, already_found=None):
        """
        Find all Bit objects that interact with this Bit through quantum
        circuit operations.
        """
        # TODO: unit test
        searched_bits = set()
        all_known_bits = { self }
        while len(searched_bits) < len(all_known_bits):
            for bit in (all_known_bits - searched_bits):
                for op in bit.operations:
                    all_known_bits |= set(op.qubits + op.promises)
                searched_bits.add(bit)
        return all_known_bits

    def as_control(self) -> _ControlBitContextManager:
        """
        Return a context manager to condition quantum gates. Use this to
        control quantum gates using the `with` statement.

        ```python
        with my_bit.as_control():
            qubit.x()  # conditioned on my_bit
        ```

        You can condition on both `Qubit` and `BitPromise` objects.
        """
        return _ControlBitContextManager(self)

class Qubit(Bit):
    """
    This is the main quPython object you'll interact with and the only object
    you should instantiate directly. Qubits start in state |0〉.

    ### Gates

    `Qubit` objects support the following single-qubit gate operations as
    methods.

    | Name  | Qiskit object                                                                           |
    |-------|-----------------------------------------------------------------------------------------|
    | `x`   | [`XGate`](https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.XGate)         |
    | `y`   | [`YGate`](https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.YGate)         |
    | `z`   | [`ZGate`](https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.ZGate)         |
    | `h`   | [`HGate`](https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.HGate)         |
    | `s`   | [`SGate`](https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.SGate)         |
    | `sdg` | [`SdgGate`](https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.SdgGate)     |
    | `t`   | [`TGate`](https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.TGate)         |
    | `tdg` | [`TdgGate`](https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.TdgGate)     |
    | `p`   | [`PhaseGate`](https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.PhaseGate) |
    | `rx`  | [`RXGate`](https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.RXGate)       |
    | `ry`  | [`RYGate`](https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.RYGate)       |
    | `rz`  | [`RZGate`](https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.RZGate)       |
    | `u`   | [`UGate`](https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.UGate)         |

    These gate methods mutate the `Qubit` object and return it so you can stack them.

    ```python
    qubit = Qubit().x().h()  # Qubit in state |->
    qubit.h()  # mutate to state |1>
    ```

    The `p`, `rx`, `ry`, `rz`, and `u` gates require angles. See their
    corresponding Qiskit objects for a description of the gates and their
    angles.

    ```python
    Qubit().rx(0.2)
    ```

    For a controlled gate, use the `as_control` method and the `with`
    statement. This will control all gates inside the context by that qubit.

    ```python
    qubit, another_qubit = Qubit(), Qubit()
    qubit.as_control():
        another_qubit.x()
    ```

    You can also control gates by passing a list of `Qubit`, `BitPromise`, and
    `bool` objects to the `conditions` argument. All conditions must be true to
    for the gate to apply.

    ```python
    qubit.x(conditions=[another_qubit, measurement_result, True])
    ```

    ### Measurement

    Use the `measure` method to return a `BitPromise`. These promises can
    control quantum gates too using the `as_control` method.
    """
    def __init__(self):
        self.operations = []
        self._create_1q_gate_methods()

    def __bool__(self):
        raise ValueError(
            "Can't cast Qubit to bool; use `.measure()` to measure"
            " the qubit instead."
        )

    def _separate_conditions(self, conditions):
        qubits = [c for c in conditions if isinstance(c, Qubit)]
        promises = [c for c in conditions if isinstance(c, BitPromise)]
        build_time_conditions = [c for c in conditions if not isinstance(c, (Qubit, BitPromise))]
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
                conditions += __active_controls__.get()
                qubits, promises, build_time_conditions = self._separate_conditions(conditions)
                if not all(build_time_conditions):
                    return
                qiskit_inst = gate(*args, **kwargs)
                if qubits:
                    qiskit_inst = qiskit_inst.control(len(qubits))
                inst = _quPythonInstruction(
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
            attr = getattr(self, name)
            attr.__doc__ = f"Apply '{name}' gate to qubit"
            attr.__annotations__["return"] = Self

    def measure(self, conditions=None) -> BitPromise:
        """
        Add measure instruction to Qubit and return BitPromise
        """
        conditions = conditions or []
        conditions += __active_controls__.get()
        qubits, promises, build_time_conditions = self._separate_conditions(conditions)
        if qubits or promises:
            raise ConditionMeasurementAtRuntimeError(ERR_MSG["ConditionMeasurementAtRuntimeError"])
        if not all(build_time_conditions):
            return
        inst = _quPythonMeasurement(self)
        self.operations.append(inst)
        return inst.promises[0]

class BitPromise(Bit):
    """
    Placeholder for qubit measurement results. You should never instantiate
    this class directly, it should only be output from `Qubit.measure`.

    When you return a `BitPromise` from an `@quantum` function, quPython finds
    the `Qubit` that created this `BitPromise` and compiles the quantum program
    needed to calculate it.

    Invert a `BitPromise` using the `~` operator. This returns a new
    `BitPromise` with an inverted value.

    ```python
    with (~bit_promise).as_control():
        # Apply gates if `bit_promise` is `False`
    ```

    <details>
    <summary>Gotchas</summary>

    After its value is determined, a `BitPromise` tries to behave as much like
    a `bool` as possible. Unfortunately, there are some quirks because
    `BitPromise` objects need to have unique hashes before circuit compilation,
    but `bool`s all have the same hash (0 or 1) and you can't change an
    object's hash without breaking basic Python functionality. The following
    code snippet shows an example.

    ```python
    # Create fulfilled qubit promise
    promise = BitPromise(None)
    promise.value = True

    # Show unexpected behavior
    promise == True  # True
    promise in (True, False)  # False
    ```

    For best results, cast to `bool` as soon as possible after the function
    completes or use the `value` attribute.

    If you have better ideas on how to handle this, let me know in an
    [issue](https://github.com/frankharkins/qupython/issues/new).
    </details>
    """

    def __init__(self, measurement_instruction, inverse=False):
        self.operations = [measurement_instruction]
        self._inverse = inverse
        self.value = None
        """
        Value of the `BitPromise`. This is `None` until the promise is
        resolved.
        """

    def __bool__(self):
        if self.value is None:
            raise BitPromiseNotResolvedError(ERR_MSG["BitPromiseNotResolved"])
        if self._inverse:
            return not self.value
        return self.value

    def __int__(self):
        return int(bool(self))

    def __eq__(self, other):
        if self.value is None:
            return id(self) == id(other)
        return bool(self) == other

    def __hash__(self):
        return id(self)

    def __repr__(self):
        if self.value is None:
            return f"BitPromise({self.operations})"
        return repr(bool(self))

    def __invert__(self) -> BitPromise:
        # TODO: This is a bit inefficient as it adds a new measurement each
        # time we invert the promise
        measurement_instruction = self.operations[0]
        new_promise = BitPromise(
            measurement_instruction,
            inverse= not self._inverse
        )
        measurement_instruction.promises.append(new_promise)
        return new_promise


class _quPythonInstruction:
    def __init__(self, qiskit_instruction, qubits, promises=[]):
        self.qiskit_instruction = qiskit_instruction
        self.qubits = qubits
        self.promises = promises

    def __repr__(self):
        return f"_quPythonInstruction({self.qiskit_instruction.name}, {self.qubits})"


class _quPythonMeasurement:
    def __init__(self, qubit):
        self.promises = [BitPromise(self)]
        self.qubits = [qubit]


class BitPromiseNotResolvedError(Exception):
    """
    For if you try to cast to `bool` before the promise has been resolved.
    """
    pass

class ConditionMeasurementAtRuntimeError(Exception):
    """
    We can't currently condition measurement operations on `Bit` objects so
    raise an exception if someone tries it.
    """
    pass

class _ControlBitContextManager:
    def __init__(self, control):
        self.control = control
    def __enter__(self):
        existing_controls = __active_controls__.get()
        self.reset_token = __active_controls__.set(existing_controls + (self.control,))
    def __exit__(self, _exc_type, _exc_value, _traceback):
        __active_controls__.reset(self.reset_token)

