from roman_converter.cli import rom_to_ar_conv


def test_rom_to_ar_conv():
    assert rom_to_ar_conv("V") == "5"
