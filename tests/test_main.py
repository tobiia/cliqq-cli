import pytest
from cliqq import main


def test_load_template(tmp_path):
    """Check load_template"""
    # Create a fake template file
    file_content = "this is meant to be inside a file!"
    tfile = tmp_path / "templates" / "starter.txt"
    tfile.parent.mkdir()
    tfile.write_text(file_content)

    # check file is loaded correctly
    prepped_template = main.load_template(tfile).strip()
    assert prepped_template == file_content
