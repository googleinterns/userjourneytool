import ujt.main
import pytest

@pytest.mark.parametrize("x", range(-10, 10))
@pytest.mark.parametrize("y", range(-10, 10))
def test_add(x, y):
    assert ujt.main.add(x, y) == x + y
