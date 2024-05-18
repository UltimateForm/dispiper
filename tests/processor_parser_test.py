from unittest.mock import patch
from discord import Embed
from config import EmbedOptions, PipelineParser, PipelineParserNode
import processors


def test_with_content_input_and_output():
    input_node = PipelineParserNode(
        "Test %{WORD:Variable1} %{WORD:Variable2}", "content"
    )

    output_node = PipelineParserNode(
        "Result variable 1: {Variable1}; variable 2: {Variable2}", "content"
    )

    parser = PipelineParser(input_node, output_node, None)
    with patch("discord.Message") as fake_discord_message:
        message = fake_discord_message.return_value
        message.content = "Test Foo Bar"
        result: str = processors.parse_message(parser, message)
        assert isinstance(result, str)
        assert result == "Result variable 1: Foo; variable 2: Bar"


def test_with_transport_props():
    input_node = PipelineParserNode(
        "Test %{WORD:Variable1} %{WORD:Variable2}", "content"
    )

    output_node = PipelineParserNode(
        "Result variable 1: {Variable1}; variable 2: {Variable2}; variable 3: {Author}",
        "content",
    )

    parser = PipelineParser(input_node, output_node, None)
    with patch("discord.Message") as fake_discord_message:
        message = fake_discord_message.return_value
        message.content = "Test Foo Bar"
        message.author.name = "JohnDoe"
        result: str = processors.parse_message(parser, message)
        assert isinstance(result, str)
        assert result == "Result variable 1: Foo; variable 2: Bar; variable 3: JohnDoe"


def test_content_input_embed_output():
    input_node = PipelineParserNode(
        "Test %{WORD:Variable1} %{WORD:Variable2}", "content"
    )

    output_node = PipelineParserNode(["Variable1", "Variable2"], "embed")

    parser = PipelineParser(input_node, output_node, None)
    with patch("discord.Message") as fake_discord_message:
        message = fake_discord_message.return_value
        message.content = "Test Foo Bar"
        result: Embed = processors.parse_message(parser, message)
        assert isinstance(result, Embed)
        assert len(result.fields) == 2
        assert result.fields[0].name == "Variable1"
        assert result.fields[0].value == "Foo"
        assert result.fields[1].name == "Variable2"
        assert result.fields[1].value == "Bar"


def test_content_input_embed_output_and_transport_props():
    input_node = PipelineParserNode(
        "Test %{WORD:Variable1} %{WORD:Variable2}", "content"
    )

    output_node = PipelineParserNode(["Variable1", "Variable2", "Author"], "embed")

    parser = PipelineParser(input_node, output_node, None)
    with patch("discord.Message") as fake_discord_message:
        message = fake_discord_message.return_value
        message.content = "Test Foo Bar"
        message.author.name = "JohnDoe"
        result: Embed = processors.parse_message(parser, message)
        assert isinstance(result, Embed)
        assert len(result.fields) == 3
        assert result.fields[0].name == "Variable1"
        assert result.fields[0].value == "Foo"
        assert result.fields[1].name == "Variable2"
        assert result.fields[1].value == "Bar"
        assert result.fields[2].name == "Author"
        assert result.fields[2].value == "JohnDoe"


def test_embed_input_and_output():
    embed = Embed()
    embed.add_field(name="Field1", value="Test Foo Bar")
    embed.add_field(name="Field2", value="Lorem Test Ipsum")
    input_node = PipelineParserNode(
        {
            "Field1": "Test %{WORD:Variable1} %{WORD:Variable2}",
            "Field2": "%{WORD:Variable3} Test %{WORD:Variable4}",
        },
        "embed",
    )
    ouput_node = PipelineParserNode(
        pattern=["Variable1", "Variable2", "Variable3", "Variable4"], msg_type="embed"
    )
    parser = PipelineParser(input_node, ouput_node, None)
    with patch("discord.Message") as fake_discord_message:
        message = fake_discord_message.return_value
        message.embeds = [embed]
        result: Embed = processors.parse_message(parser, message)
        assert isinstance(result, Embed)
        assert len(result.fields) == 4
        assert result.fields[0].name == "Variable1"
        assert result.fields[0].value == "Foo"
        assert result.fields[1].name == "Variable2"
        assert result.fields[1].value == "Bar"
        assert result.fields[2].name == "Variable3"
        assert result.fields[2].value == "Lorem"
        assert result.fields[3].name == "Variable4"
        assert result.fields[3].value == "Ipsum"


def test_embed_input_content_output():
    embed = Embed()
    embed.add_field(name="Field1", value="Test Foo Bar")
    embed.add_field(name="Field2", value="Lorem Test Ipsum")
    input_node = PipelineParserNode(
        {
            "Field1": "Test %{WORD:Variable1} %{WORD:Variable2}",
            "Field2": "%{WORD:Variable3} Test %{WORD:Variable4}",
        },
        "embed",
    )
    ouput_node = PipelineParserNode(
        pattern="Result variable 1: {Variable1}; variable 2: {Variable2}; variable 3: {Variable3}, variable 4: {Variable4}",
        msg_type="content",
    )
    parser = PipelineParser(input_node, ouput_node, None)
    with patch("discord.Message") as fake_discord_message:
        message = fake_discord_message.return_value
        message.embeds = [embed]
        result: Embed = processors.parse_message(parser, message)
        assert isinstance(result, str)
        assert (
            result
            == "Result variable 1: Foo; variable 2: Bar; variable 3: Lorem, variable 4: Ipsum"
        )


def test_embed_input_content_output_and_transport_props():
    embed = Embed()
    embed.add_field(name="Field1", value="Test Foo Bar")
    embed.add_field(name="Field2", value="Lorem Test Ipsum")
    input_node = PipelineParserNode(
        {
            "Field1": "Test %{WORD:Variable1} %{WORD:Variable2}",
            "Field2": "%{WORD:Variable3} Test %{WORD:Variable4}",
        },
        "embed",
    )
    ouput_node = PipelineParserNode(
        pattern="Result variable 1: {Variable1}; variable 2: {Variable2}; variable 3: {Variable3}; variable 4: {Variable4}; Author: {Author}",
        msg_type="content",
    )
    parser = PipelineParser(input_node, ouput_node, None)
    with patch("discord.Message") as fake_discord_message:
        message = fake_discord_message.return_value
        message.embeds = [embed]
        message.author.name = "JohnDoe"
        result: Embed = processors.parse_message(parser, message)
        assert isinstance(result, str)
        assert (
            result
            == "Result variable 1: Foo; variable 2: Bar; variable 3: Lorem; variable 4: Ipsum; Author: JohnDoe"
        )


def test_no_parser_nodes_for_content():
    parser = PipelineParser(None, None, None)
    with patch("discord.Message") as fake_discord_message:
        message = fake_discord_message.return_value
        message.content = "Test Foo Bar"
        result: str = processors.parse_message(parser, message)
        assert isinstance(result, str)
        assert result == "Test Foo Bar"


def test_no_parser_nodes_for_embed():
    parser = PipelineParser(None, None, None)
    embed = Embed(title="TestEmbed")
    embed.add_field(name="Field1", value="Test Foo Bar")
    embed.add_field(name="Field2", value="Lorem Test Ipsum")
    with patch("discord.Message") as fake_discord_message:
        message = fake_discord_message.return_value
        message.content = None
        message.embeds = [embed]
        result: Embed = processors.parse_message(parser, message)
        assert isinstance(result, Embed)
        assert result == embed


def test_no_parser_nodes_for_embed_with_embed_options():
    parser = PipelineParser(
        None, None, EmbedOptions("ChangedTitle", 11342935, "ChangedEmbedDescription")
    )
    embed = Embed(title="TestEmbed")
    embed.add_field(name="Field1", value="Test Foo Bar")
    embed.add_field(name="Field2", value="Lorem Test Ipsum")
    with patch("discord.Message") as fake_discord_message:
        message = fake_discord_message.return_value
        message.content = None
        message.embeds = [embed]
        result: Embed = processors.parse_message(parser, message)
        assert isinstance(result, Embed)
        assert result == embed
        assert result.title == "ChangedTitle"
        assert result.color.value == 11342935
        assert result.description == "ChangedEmbedDescription"
