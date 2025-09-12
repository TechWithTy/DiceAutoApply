import json
from pathlib import Path
from typing import Dict, Any


def load_prompt_template(template_name: str) -> str:
    """Load a prompt template from the templates directory."""
    templates_dir = Path(__file__).parent / 'templates'
    template_path = templates_dir / f"{template_name}.txt"
    return template_path.read_text(encoding='utf-8')


def render_prompt(template: str, variables: Dict[str, Any]) -> str:
    """Render a prompt template with provided variables."""
    return template.format(**variables)


def save_prompt_output(output: str, filename: str):
    """Save prompt output to the outputs directory."""
    outputs_dir = Path(__file__).parent / 'outputs'
    outputs_dir.mkdir(exist_ok=True)
    output_path = outputs_dir / filename
    output_path.write_text(output, encoding='utf-8')


def load_prompt_config(config_name: str) -> Dict[str, Any]:
    """Load a prompt configuration JSON file."""
    configs_dir = Path(__file__).parent / 'configs'
    config_path = configs_dir / f"{config_name}.json"
    return json.loads(config_path.read_text(encoding='utf-8'))
