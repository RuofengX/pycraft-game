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
from typing import List, TypeGuard, Type
from enum import Enum
from threading import Lock
from collections import OrderedDict
from dataclasses import dataclass

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
    """MsgInboxMixin provides a basic inbox function and a static status enum.

    An entity could inheritage this mixin to gain the abiliaty for receiving msg.
    Or, like a duck type, if an entity have msg_inbox property, it could receive msg.

    A entity whit MsgInbox must have an position, or msg sent to it will always failure.
    """

    class MsgStatus(Enum):
        """Enum of MsgStatus"""

        PENDING = "Msg is in outbox and waiting for next msg_tick."
        SENT = "Msg is successfuly sent to target."
        NO_INBOX = "Target is found in send-radius, \
            but target does not have property msg_inbox."
        NOT_FOUND = (
            "Target is not found in send radius. Ensure your target_id is correct."
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.msg_inbox: List[str] = []


class MsgMixin(MsgInboxMixin, Character):
    # TODO: test needed
    """MsgMixin is a module provided basic message of an entity.

    Like a visiable-light shape of a thing in real world.

    It provides a basic level control of send & receive msg.
    Extra limits and restricts should be implemented on higher level class.

    MsgPayload is a namedtuple with 4 tags: target, content, radius, result.
    MsgPayload is only used in msg_outbox stack.
    """

    @dataclass
    class MsgPayload(OrderedDict):
        """MsgPayload is a namedtuple with 4 tags: target, content, radius, result.

        MsgPayload is only used in msg_outbox stack.
        """

        target_eid: int
        content: str
        radius: float
        result: MsgInboxMixin.MsgStatus = MsgInboxMixin.MsgStatus.PENDING

        def status_update(self, status: MsgInboxMixin.MsgStatus):
            self.result = status

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.msg_name = "<Not Set>"
        self.msg_outbox: List[MsgMixin.MsgPayload] = []
        self.__msg_outbox_lock = Lock()

    def msg_send(self, target_eid: int, content: str, radius: float) -> None:
        """Send message to other entity with target_eid,
        target entity must have msg_mixin.

        Message will be limited in radius.
        """
        payload = self.MsgPayload(target_eid=target_eid, content=content, radius=radius)
        with self.__msg_outbox_lock:
            self.msg_outbox.append(payload)

    @classmethod
    def msg_target_has_inbox(cls, target: Character) -> TypeGuard[Type[MsgInboxMixin]]:
        """Check target character has inbox"""
        return hasattr(target, "msg_inbox")

    def msg_tick(self, belong: World) -> None:
        with self.__msg_outbox_lock:
            for p in self.msg_outbox:
                if p.result is self.MsgStatus.PENDING:
                    """Only send msg pending"""
                    if belong.get_entity(
                        eid=p.target_eid
                    ):  # Entity in World.entity_dict is always a Character
                        """Check target exists silent"""
                        dis = belong._get_natural_distance(p.target_eid, self)

                        if dis is None:
                            p.status_update(self.MsgStatus.NOT_FOUND)
                            return

                        if dis <= p.radius:
                            """Only send msg in radius"""
                            target = belong.entity_dict[p.target_eid]
                            if self.msg_target_has_inbox(target):  # duck type
                                target.msg_inbox.append(p.content)

                                p.status_update(self.MsgStatus.SENT)
                            else:
                                p.status_update(self.MsgStatus.NO_INBOX)
                        else:
                            p.status_update(self.MsgStatus.NOT_FOUND)
                    else:
                        p.status_update(self.MsgStatus.NOT_FOUND)
