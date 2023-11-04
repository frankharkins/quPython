import unittest
from pathlib import Path
from textwrap import dedent
from qupython import Qubit, quantum

README_PATH = Path(__file__).parent.parent / Path("README.md")

class TestReadmeInSync(unittest.TestCase):
    """
    Make sure these code examples appear in README.md
    """
    def test_readme_in_sync(self):
        with open(__file__, "r") as f:
            source_code = f.read()
        delimiter = "# === {} code example ==="
        snippets = [
            dedent(snippet.split(delimiter.format("End"))[0])
            for snippet in source_code.split(delimiter.format("Begin"))[1:]
        ]
        with open(README_PATH) as f:
            readme = f.read()
        for snippet in snippets:
            self.assertIn(
                snippet,
                readme
            )


class TestReadmeExamples(unittest.TestCase):
    def test_simple_example(self):

        # === Begin code example ===
        from qupython import Qubit, quantum

        @quantum
        def random_bit():
            qubit = Qubit()         # Allocate new qubit
            qubit.h()               # Mutate qubit
            return qubit.measure()  # Measure qubit to bool
        # === End code example ===

        self.assertIn(random_bit(), (True, False))
