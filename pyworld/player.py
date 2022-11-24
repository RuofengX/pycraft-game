from pyworld.control import ControlMixin
from pyworld.modules import CargoMixin, MsgMixin, StructMixin
from pyworld.world import Character, World


class Player(MsgMixin, StructMixin, CargoMixin, ControlMixin, Character):
    def __init__(self, *, username: str, passwd: str, world: World, **kwargs):
        super().__init__(**kwargs)
        self.username = username
        self.passwd = passwd
        world.player_dict[username] = self
