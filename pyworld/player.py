from pyworld.modules.beings import MsgMixin
from pyworld.world import Character


class Player(MsgMixin, Character):
    def __init__(self, username: str, passwd_with_salt: str, **kwargs):
        super().__init__(**kwargs)
        self.username = username
        self.passwd_with_salt = passwd_with_salt
