import re

from discord import Embed


def regex_match(expr: str, value: str):
    return bool(re.search(expr, value))


# doing this because i've seen discord allows embeds without the expected fields() array
def embed_to_dict(embed: Embed):
    fields = embed.fields
    if fields:
        return dict((field.name, field.value) for field in fields)
    embed_descr = embed.description
    lines = embed_descr.split("\n")
    pairs = [line.split(":** ") for line in lines if line]
    dictionary = dict((key.lstrip("**"), value) for [key, value] in pairs)
    return dictionary
