"""Every being contains their 'function' module.
Those modules are provided with Mixin classes.
Each Mixin act as a set of ports, like Interface in Java.

Mixin modules named as <Name>Mixin,
variables named as <module_name>_<variable_name>,
methods named as <module_name>_<method_name>.

Instance will initiate first by default class, e.g. Character, then the Mixin class.
Entity instance will run every method named after with '_tick' in every tick.

The '_tick' method must have two positional arguments, which is:
1. instance itself;
2. (Optional)the belonging of this instance. In most case is the Continuum instance.
And return None.
"""
from collections import namedtuple
from typing import List, TypeGuard, Type

from objprint import op  # type:ignore

from world import Entity, World, Character

# TODO: Use Metaclass to regulate those generate of Mixin module.


class DebugMixin:
    """For those needs"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__DEBUG_FLAG = True

    def debug_tick(self, belong=Entity):
        op(self)
        op(belong)


class MsgInboxMixin(Character):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.msg_inbox: List[str] = []


class MsgMixin(MsgInboxMixin, Character):
    # TODO: test needed
    """MsgMixin is a module provided basic message of an entity.

    Like a visiable-light shape of a thing in real world.

    It provides a basic level control of send & receive msg.
    More limits and restricts should be implemented on higher level class.

    MsgPayload is a namedtuple with 4 tags: target, content, radius, result.
    MsgPayload is only used in msg_outbox stack.
    """

    class MsgPayload(namedtuple("MsgPayload", "target content radius result")):
        """MsgPayload is a namedtuple with 4 tags: target, content, radius, result.

        MsgPayload is only used in msg_outbox stack.
        """

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._replace(result="PENDING")

        def update(self, status: str):
            self._replace(result=status)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.msg_name = "<Not Set>"
        self.msg_outbox: List[MsgMixin.MsgPayload] = []

    def msg_send(self, eid: int, content: str, radius: float):
        """Send message to other entity, Other entity must have msg_mixin.
        Message will be limited in radius."""
        payload = self.MsgPayload(
            target=eid, content=content, radius=radius, result="PENDING"
        )
        self.msg_outbox.append(payload)

    def msg_target_has_inbox(self, target: Character) -> TypeGuard[Type[MsgInboxMixin]]:
        """Check target character has inbox"""
        return hasattr(target, "msg_inbox")

    def msg_tick(self, belong: World):
        for payload in self.msg_outbox:
            target_eid, content, radius, result = payload
            if result in ["PENDING", "NOT_FOUND"]:
                """Only send msg pending"""
                if belong.get_entity(eid=target_eid):
                    """Check target exists silent"""
                    dis = belong._get_natural_distance(target_eid, self)
                    if dis <= radius:
                        """Only send msg in radius"""
                        target = belong.entity_dict[target_eid]
                        if self.msg_target_has_inbox(target):  # duck type
                            target.msg_inbox.append(content)
                            payload.update("SENT")
                        else:
                            payload.update("NO_INBOX")
                    else:
                        payload.update("NOT_FOUND")
                else:
                    payload.update("NOT_FOUND")
