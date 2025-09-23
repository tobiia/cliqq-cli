from cliqq import main


def test_load_template(tmp_path, file_content):
    """Check load_template"""
    # Create a fake template file
    tfile = tmp_path / "templates" / "starter.txt"
    tfile.parent.mkdir()
    tfile.write_text(file_content)

    # check file is loaded correctly
    prepped_template = main.load_template(tfile).strip()
    assert prepped_template == file_content
