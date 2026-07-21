from pathlib import Path

from jinja2 import Environment
from jinja2 import FileSystemLoader


class TemplateRenderer:

    def __init__(self):

        template_path = (
            Path(__file__).parent.parent / "templates"
        )
        print(template_path)
        print(template_path.exists())

        self.environment = Environment(
            loader=FileSystemLoader(template_path),
            autoescape=True
        )

    def render(self, template_name: str, context: dict):

        template = self.environment.get_template(template_name)

        return template.render(**context)