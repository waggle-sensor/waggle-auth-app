# NOTE(sean) This is a replacement for the now deprecated TestCase.assertDictContainsSubset as of Python 3.12.
def assertDictContainsSubset(subset, dictionary):
    for key, value in subset.items():
        assert key in dictionary
        assert dictionary[key] == value
