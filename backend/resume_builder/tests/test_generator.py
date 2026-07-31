import os
import json
import pytest
from generator import generate_resume

# Define paths relative to the resume_builder root
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
RESUME_DATA_PATH = os.path.join(DATA_DIR, "base.json")
CL_DATA_PATH = os.path.join(DATA_DIR, "cover_letter_base.json")

@pytest.fixture
def resume_data():
    with open(RESUME_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def cl_data():
    with open(CL_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def test_generate_resume_standard(resume_data, tmp_path):
    output_pdf = tmp_path / "test_resume.pdf"
    generate_resume("standard", resume_data, str(output_pdf))
    
    assert output_pdf.exists()
    assert output_pdf.stat().st_size > 0

def test_generate_cover_letter_standard(cl_data, tmp_path):
    output_pdf = tmp_path / "test_cl.pdf"
    generate_resume("cover_letter", cl_data, str(output_pdf))
    
    assert output_pdf.exists()
    assert output_pdf.stat().st_size > 0

def test_generator_fallback(resume_data, tmp_path):
    # Testing that an unknown template falls back to standard resume
    output_pdf = tmp_path / "test_fallback.pdf"
    generate_resume("unknown_template", resume_data, str(output_pdf))
    
    assert output_pdf.exists()
    assert output_pdf.stat().st_size > 0
