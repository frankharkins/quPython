# Experimental extra-long error messages
# fmt: off

from textwrap import dedent

ERR_MSG = {
  "BitPromiseNotResolved":
  """
  You can't cast BitPromise to a bool until it's resolved.

  You're trying to cast a BitPromise (the output of .measure()) to a bool, but
  BitPromise objects don't have a value until after the function completes.

    @quantum
    def random_action():
        a = Qubit()
        if a.measure():  # Problem
            do_thing()
        return

  To fix this, try to move that logic outside the @quantum function, like so:

    @quantum
    def random_bit():
        a = Qubit()
        return a.measure()

    if random_bit():
        do_thing()

  There is an exception to this: The quPython compiler recognises BitPromise
  objects that condition qubit gates, so you can do the following.

    a, b = Qubit(), Qubit()
    # Measure one qubit and condition X-gate on measurement result
    promise = a.measure()
    b.x(conditions=[promise])
  """,

  "ReturnQubitFromQuantumFunction":
  """
  Can't return a Qubit from a @quantum function; did you mean to return Qubit.measure()?

  This means you're doing something like this:

    @quantum
    def thing():
        a = Qubit()
        return a  # Problem

  To fix this, make sure all qubit operations happen within the @quantum
  function, and that the function only returns classical data.

    @quantum
    def thing():
        a = Qubit()         # Create new qubit
        a.h()               # Process it
        return a.measure()  # Return classical bit

  The problem is quPython needs to compile the @quantum function into a quantum
  circuit. Qubits are reset after the circuit is finished, so you can't
  continue processing a Qubit after it's been compiled and executed.

  Compilation and execution happens when the @quantum function completes, so
  quPython raises this message to prevent you from accidentally handling
  compiled Qubit objects.
  """,

  "CantSearchObjectForPromises":
  """
  Can't search through object {obj} for BitPromise objects.

  When a @quantum function returns something, quPython intercepts it and
  searches for any BitPromise objects. It then compiles and executes the
  quantum program needed to fulfil these promises.

  For some reason, quPython can't search the object(s) you're returning.
  Consider returning a different data structure, or raising a bug report if you
  belive this object should be searchable.
  """,

  "CastQubitToBool":
  """
  Can't cast Qubit to bool.

  You're trying to do something like this:

    @quantum
    def thing():
        a = Qubit()
        is_true = bool(a)  # Problem
        ...

  The problem is quPython only compiles and executes the quantum part of the
  function after the function completes. You're trying to convert the qubit to
  a Python data type before any quantum processing has happened. To fix this,
  return the result of Qubit.measure(), and do your regular Python processing
  outside the @quantum function.

    @quantum
    def thing():
        a = Qubit()
        return a.measure()
    is_true = bool(thing())
  """,

  "CompileFunctionBeforeRunning":
  """
  You need to compile this function before running it.

  To fix, do:

      your_function.compile( <function-args-here> )

  This will compile the function but not execute any circuits.
  """,

  "ConditionMeasurementAtRuntimeError":
  """
  You're trying to condition a Qubit measurement on either another Qubit, or on
  the result of a Qubit measurement. Conditioning a measurement on a Qubit is
  impossible, and quPython doesn't support conditioning measurements on Qubit
  measurements yet. The problem occurs when you do something like this:

    @quantum
    def my_func():
        a, b = Qubit(), Qubit()
        with a.as_control():
            b.x()
            output = b.measure()  # problem
        return output

  To resolve this, move the measurement out of the `with` block.
  """
}

signoff = """
---

These long error messages are experimental; let me know on GitHub if they're
helpful or annoying.

https://github.com/frankharkins/quPython
"""

ERR_MSG = { name: dedent(msg).lstrip() + signoff for name, msg in ERR_MSG.items() }
