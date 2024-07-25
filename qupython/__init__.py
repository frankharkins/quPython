"""
.. include:: ../README.md
   :start-line: 2

<br>
<br>

## API documentation

The rest of the page is the API documentation for the two main quPython
imports: `Qubit` and `quantum`. You can also import `BitPromise` objects for
type annotations from `qupython.typing`.

"""
__docformat__ = "restructuredtext"
from .qubit import Qubit
from .decorator import quantum

__all__ = ["Qubit", "quantum", "qubit", "typing", "function"]
