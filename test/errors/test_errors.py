import unittest
import infinitory.errors
import sample


class MyTest(unittest.TestCase):
    def test_error_message_cleaner(self):

        errorParser = infinitory.errors.ErrorParser()

        self.assertEqual(errorParser.clean_error_message("Hello"), "Hello")

        self.assertEqual(
            errorParser.clean_error_message("Could not retrieve catalog from remote server: Error 500 on SERVER: Server Error: Evaluation Error: Error while evaluating a Function Call, Untrusted facts (left) don't match values from certname (right) owaijefoeiawjfoiewjf"),
            "Could not retrieve catalog from remote server: Error 500 on SERVER: Server Error: Evaluation Error: Error while evaluating a Function Call, Untrusted facts (left) don't match values from certname (right)"
        )

    def test_other_prefixing(self):
        """ The cell formatter expects that all values have a prefix associated
            with them. This checks that the errorParser properly adds that
            prefix. """

        errorParser = infinitory.errors.ErrorParser()

        input = ["1", "2"]

        errorParser.set_all_errors(input)
        errorParser.set_unique_errors(input)

        self.assertEqual(
            [ { "other": "1" }, { "other": "2" } ],
            errorParser.all_errors()
        )
        self.assertEqual(
            [ { "other": "1" }, { "other": "2" } ],
            errorParser.unique_errors()
        )
