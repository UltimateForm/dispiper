import re


def regex_match(expr: str, value: str):
    return bool(re.search(expr, value))


# doing this because i've seen discord allows embeds without the expected fields() array
def embed_to_dict(embed_descr: str):
    lines = embed_descr.split("\n")
    pairs = [line.split(":** ") for line in lines if line]
    dictionary = dict((key.lstrip("**"), value) for [key, value] in pairs)
    return dictionary
