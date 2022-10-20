from world import Character, Vector


class Player(Character):
    """A player is a special kind of character

    Any player function must be implemented in this class"""
    def __init__(self, eid: int, pos: Vector, velo: Vector = Vector(0, 0, 0)):
        super().__init__(eid=eid, pos=pos, velo=velo)
