import re
import string


letter_map = {k: i for i, k in enumerate(string.ascii_letters + string.digits)}


def letter_gt(a: str, b: str):
    """Compare two letters, returning True if a > b"""
    n_a = letter_map[a]
    n_b = letter_map[b]

    if n_a == n_b:
        return None

    return n_a > n_b


def get_number(val: str) -> int:
    return int(re.search(r"\d+", val).group())


def can_continue(a, b, pointer):
    try:
        a_letter = a[pointer]
    except IndexError:
        return False

    try:
        b_letter = b[pointer]
    except IndexError:
        return True

    if a_letter == b_letter:
        pointer += 1

        if a_letter == "-":
            return is_a_gt_b(a[pointer:], b[pointer:])

        return

    if a_letter == '-':
        return False

    if b_letter == '-':
        return True

    if a_letter.isdigit() and b_letter.isdigit():
        return int(a_letter) > int(b_letter)

    return letter_gt(a_letter, b_letter)


def is_a_gt_b(a: str, b: str):
    """Compare two strings, returning True if a > b"""
    if a == b:
        return False

    if a.isdigit() and b.isdigit():
        return int(a) > int(b)

    if get_number(a) > get_number(b):
        return True
    elif get_number(a) < get_number(b):
        return False

    pointer = 0
    while True:
        can_continue_val = can_continue(a, b, pointer)
        if can_continue_val is not None:
            return can_continue_val

        pointer += 1
