class TypeA():
    pass


class TypeB(TypeA):
    pass


class TestA():
    def __init__(self, args_1: TypeA):
        pass


TestA(TypeB())
