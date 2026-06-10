"""Safe prompt rendering — avoids str.format() breaking on JSON braces."""


def render_prompt(template: str, **variables: object) -> str:
    result = template
    for key, value in variables.items():
        result = result.replace("{" + key + "}", str(value))
    return result
