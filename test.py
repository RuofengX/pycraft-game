from typing import Callable, TypeAlias


class Q:
    pass


class T(Q):
    pass


class P(T):
    pass


TestA: TypeAlias = Callable[[T], None]

TestB: TypeAlias = Callable[[P], None]


def test_method(f: Q) -> None:
    pass


def test_method2(f: T) -> None:
    pass


def test_method3(f: P) -> None:
    pass


def test_A(method: TestA):
    pass


test_A(test_method)
test_A(test_method2)
test_A(test_method3)


def test_B(_: T):
    pass


test_B(Q())
test_B(T())
test_B(P())
