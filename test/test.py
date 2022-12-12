from typing import Generic, TypeVar, get_type_hints


class TypeA:
    pass


class TypeB(TypeA):
    pass


class TestA:
    def __init__(self, args_1: TypeA):
        pass


TestA(TypeB())


T = TypeVar("T")


class G(Generic[T]):
    def __init__(self) -> None:
        print(get_type_hints(G))


if __name__ == "__main__":
    a: G[int] = G()
