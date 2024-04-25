import unittest
import unittest.mock
from discord import Embed
import processors
from config import PipelineParser, PipelineParserNode


class TestParser(unittest.TestCase):

    def test_with_content_input_and_output(self):
        input_node = PipelineParserNode(
            "Test %{WORD:Variable1} %{WORD:Variable2}", "content"
        )

        output_node = PipelineParserNode(
            "Result variable 1: {Variable1}; variable 2: {Variable2}", "content"
        )

        parser = PipelineParser(input_node, output_node)
        with unittest.mock.patch("discord.Message") as mock_message:
            message = mock_message.return_value
            message.content = "Test Foo Bar"
            result: str = processors.parse_message(parser, message)
            self.assertIsInstance(result, str)
            self.assertEqual(result, "Result variable 1: Foo; variable 2: Bar")

    def test_with_content_input_and_embed_output(self):
        input_node = PipelineParserNode(
            "Test %{WORD:Variable1} %{WORD:Variable2}", "content"
        )

        output_node = PipelineParserNode(["Variable1", "Variable2"], "embed")

        parser = PipelineParser(input_node, output_node)
        with unittest.mock.patch("discord.Message") as mock_message:
            message = mock_message.return_value
            message.content = "Test Foo Bar"
            result: Embed = processors.parse_message(parser, message)
            self.assertIsInstance(result, Embed)
            self.assertEqual(len(result.fields), 2)
            self.assertEqual(result.fields[0].name, "Variable1")
            self.assertEqual(result.fields[0].value, "Foo")
            self.assertEqual(result.fields[1].name, "Variable2")
            self.assertEqual(result.fields[1].value, "Bar")


if __name__ == "__main__":
    unittest.main()
