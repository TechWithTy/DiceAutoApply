import json
import argparse
import sys
import os
from typing import Dict, Any

# Ensure we can import templates when imported as a module
sys.path.append(os.path.dirname(__file__))

# Import the original template's build function
from templates.resumes.standard import build_resume as build_standard_resume
from templates.cover_letters.standard import build_cover_letter as build_standard_cover_letter

def generate_resume(template_id: str, data: Dict[str, Any], out_path: str):
    if template_id == "standard":
        build_standard_resume(data, out_path)
    elif template_id == "cover_letter":
        build_standard_cover_letter(data, out_path)
    else:
        print(f"Template '{template_id}' not found. Defaulting to 'standard'.")
        build_standard_resume(data, out_path)

def main():
    parser = argparse.ArgumentParser(description="Resume Generator")
    parser.add_argument("input", help="Path to input JSON file")
    parser.add_argument("output", help="Path to output PDF file")
    parser.add_argument("--template", "-t", default="standard", help="Template to use (e.g., standard)")
    
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    generate_resume(args.template, data, args.output)
    print(f"Generated: {args.output} using template: {args.template}")

if __name__ == "__main__":
    main()
