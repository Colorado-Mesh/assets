import math


def sqrt_curve(_input: float, _max: float) -> float:
    return math.sqrt(_input / _max) * 10


def double_sqrt_curve(_input: float, _max: float) -> float:
    return sqrt_curve(
        _input=sqrt_curve(
            _input=_input, _max=_max),
        _max=10,
    )


def cap_value(score: float, _max: float = 10, _min: float = 0) -> float:
    """Cap a value between min and max"""
    return max(_min, min(score, _max))


def safe_log2(value: float) -> float:
    """Calculate the base-2 logarithm of a value, preventing errors on input 1"""
    return math.log2(max(1, value))


def safe_log(value: float) -> float:
    """Calculate the logarithm of a value, preventing errors on input 1"""
    return math.log(max(1, value))


def non_zero(value: float, replacement: float = 1) -> float:
    """Ensure a value is non-zero to prevent division errors"""
    return max(replacement, value)
