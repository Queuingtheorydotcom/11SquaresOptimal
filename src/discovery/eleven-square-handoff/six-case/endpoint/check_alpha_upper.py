"""Standard-library rational proof that Trump's side is below the charge gate.

The construction has t as the unique root of M on (9/25, 37/100),
and side alpha = (6t+4)/(1+2t-t²).  This script independently checks
the needed root isolation, polynomial identity, and comparison.
"""

from fractions import Fraction as F

M_DESC = (5, -10, -2, 14, 12, -6, 2, 2, -1)
P_DESC = (1, -20, 178, -842, 1923, -496, -6754, 12420, -6865)
U = F(387708359002281417731, 10**20)


def value(coefficients, x):
    result = F(0)
    for coefficient in coefficients:
        result = result * x + coefficient
    return result


def interval_value(coefficients, left, right):
    lower = upper = F(0)
    for coefficient in coefficients:
        products = (lower * left, lower * right, upper * left, upper * right)
        lower, upper = min(products) + coefficient, max(products) + coefficient
    return lower, upper


def multiply(a, b):
    result = [F(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            result[i + j] += x * y
    return result


def add(a, b):
    result = [F(0)] * max(len(a), len(b))
    for i, x in enumerate(a):
        result[i] += x
    for i, x in enumerate(b):
        result[i] += x
    return result


def power(a, exponent):
    result = [F(1)]
    for _ in range(exponent):
        result = multiply(result, a)
    return result


def remainder(numerator, divisor):
    result = list(numerator)
    while len(result) >= len(divisor):
        scale = result[-1] / divisor[-1]
        offset = len(result) - len(divisor)
        for i, coefficient in enumerate(divisor):
            result[offset + i] -= scale * coefficient
        while result and result[-1] == 0:
            result.pop()
    return result


def main():
    derivative_m = tuple((8 - i) * M_DESC[i] for i in range(8))
    assert interval_value(derivative_m, F(36, 100), F(37, 100))[0] > 0
    left_t, right_t = F(365, 1000), F(366, 1000)
    assert value(M_DESC, left_t) < 0 < value(M_DESC, right_t)

    numerator, denominator = [F(4), F(6)], [F(1), F(2), F(-1)]
    polynomial = [F(0)]
    for exponent, coefficient in enumerate(reversed(P_DESC)):
        term = multiply(power(numerator, exponent), power(denominator, 8 - exponent))
        polynomial = add(polynomial, [coefficient * x for x in term])
    assert not remainder(polynomial, list(map(F, reversed(M_DESC))))

    def side(t):
        return (6 * t + 4) / (1 + 2 * t - t * t)

    # 6t²+8t−2 is positive on this interval, so side(t) increases.
    assert 6 * left_t**2 + 8 * left_t - 2 > 0
    assert F(3876, 1000) < side(left_t) < side(right_t) < F(3878, 1000)

    derivative_p = tuple((8 - i) * P_DESC[i] for i in range(8))
    left_x = F(3876, 1000)
    step = F(1, 10000)
    # Interval Horner proves P' strictly positive over the entire range.
    for i in range(20):
        assert interval_value(derivative_p, left_x + i * step,
                              left_x + (i + 1) * step)[0] > 0
    assert F(3876, 1000) < U < F(3878, 1000)
    assert value(P_DESC, U) > 0
    # P(alpha)=0 by the verified polynomial identity. Since both alpha
    # and U are in the monotonic interval, P(U)>0 implies alpha<U.
    print("EXACT_ALPHA_BELOW_GATE_PASS", str(U))


if __name__ == "__main__":
    main()
