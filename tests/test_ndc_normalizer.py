from ndc.normalizer import normalize_ndc_to_11

def test_normalize_ndc_to_11():
    assert normalize_ndc_to_11("1234-5678-90") == "01234567890"
    assert normalize_ndc_to_11("01234567890") == "01234567890"
