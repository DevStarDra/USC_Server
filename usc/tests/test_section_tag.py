from utils.sort import letter_gt, is_a_gt_b, get_number
import pytest


@pytest.mark.parametrize(
    "a, expected",
    [
        ("1200e", "1200"),
        ("1400Z", "1400"),
        ("1400Z-2", "1400"),
        ("140Z-20", "140"),
    ]
)
def test_get_number_from_tag(a, expected):
    assert get_number(a) == int(expected)


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ('a', 'b', False),
        ('b', 'a', True),
        ('a', 'a', None),
        ('a', 'A', False),
        ('A', 'a', True),
        ('Z', 'a', True),
        ('z', 'A', False),
        ('a', 'z', False),
    ]
)
def test_letter_gt(a, b, expected):
    assert letter_gt(a, b) is expected


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("1Z", "4Z", False),
        ("4Z", "1Z", True),
        ("1aZ", "1AZ", False),
        ("1AZ", "1aZ", True),
        ("1233", "1400Z-2", False),
        ("1400Z-2", "1233", True),
        ("1400Z-2", "123356", False),
        ("1400Z", "1400Z-2", False),
        ("1400Z-2", "1400Z", True),
        ("1409Z-2", "1400Z-2A", True),
        ("1409Z-2b", "1409Z-2B", False),
        ("1409Z-2B", "1409Z-2B", False),
        ("140Z-2", "1400Z", False),
        ("1400Z", "1400Z", False),
        ("1400Z-2", "1400Z-2", False),
        ("1200e", "1200", True),
        ("1200", "1200e", False),
        ("1200e", "1200e", False),
        ("1200e", "1400Z", False),
        ("1400Z", "1200e", True),
        ("1200e", "1400Z-2", False),
        ("1400Z-2", "1200e", True),
    ]
)
def test_section_tag_gt(a, b, expected):
    assert is_a_gt_b(a, b) == expected
