"""
.. include:: ../README.md
   :start-line: 2

## API documentation

"""
__docformat__ = "restructuredtext"
from .qubit import Qubit
from .decorator import quantum

__all__ = ["Qubit", "quantum", "qubit", "typing", "function"]
