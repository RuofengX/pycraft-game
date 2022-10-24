"""
# beings.py

## Implements multiple functions for entities in the pycraft

Every being or entity have their own property or method,
but some of these functions are same. So we write those same
reuseable function as some mixin modules.
Each mixin calss act as a set of ports, like Interface in Java.

## Name regulation

Mixin modules named as <Name>Mixin,
variables named as <module_name>_<variable_name>,
methods named as <module_name>_<method_name>,
If a mixin module needs some public type or utils, write it as a sepreate mixin,
and name them as <Name><Util_name>. Also notice that only mixin class would
be inherit to the final entity type.

For example:
    '''python

    class MsgPayload():
        ...


    class MsgMixin(Character):
        def __init__(self):
            self.msg_inbox = []

        def msg_send(self):
            ...

    '''

## The 'xxx_tick' method

Entity instance will run every method named after '_tick' in every tick.

The '_tick' method must have two positional arguments, which is:
1. instance itself, also know as `self`;
2. (Optional)the belonging of this instance. In most case is the Continuum instance.

'_tick' function return None.

## Inherit order

If a mixin module(class) is only available to some specific entity type, inherit it,
like `class MsgMixin(Character)` means that MsgMixin could only apply to the type
of `Character`.

Entity instance will initiate first by mixin classes, then the entity class.
For example, an entity instance with MsgMixin and Character should wrote in these:
`class CharacterWithMsgMixin(MsgMixin, Character)`

"""

from typing import List, TypeGuard, Type
from enum import Enum
from threading import Lock
from dataclasses import dataclass
import uuid

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.msg_inbox: List[str] = []


class MsgStatus(Enum):
    """Enum of MsgStatus"""

    PENDING = "Msg is in outbox and waiting for next msg_tick."
    SENT = "Msg is successfuly sent to target."
    NO_INBOX = "Target is found in send-radius, \
        but target does not have property msg_inbox."
    NOT_FOUND = "Target is not found in send radius. Ensure your target_id is correct."
    ENSURE = "Msg is marked as ensure, will always try to send at every tick, \
        until set to SENT."


@dataclass
class MsgPayload:
    """MsgPayload is a namedtuple with 4 tags: target, content, radius, result.

    MsgPayload is a namedtuple with 4 tags: target, content, radius, result.
    MsgPayload is only used in msg_outbox stack.
    """

    target_eid: int
    content: str
    radius: float
    result: MsgStatus = MsgStatus.PENDING

    def __post_init__(self):
        self.msg_id = uuid.uuid4().int
        self.try_times : int = 0

    def status_update(self, status: MsgStatus):
        self.result = status

    def __hash__(self) -> int:
        return self.msg_id


class MsgMixin(MsgInboxMixin, Character):
    """MsgMixin is a module provided basic message of an entity.

    Like a visiable-light shape of a thing in real world.

    It provides a basic level control of send & receive msg.
    Extra limits and restricts should be implemented on higher level class.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.msg_outbox: List[MsgPayload] = []
        self.__msg_outbox_lock = Lock()

    def msg_send(self, target_eid: int, content: str, radius: float) -> int:
        """Send message to other entity with target_eid,
        target entity must have msg_mixin.

        Message will be limited in radius.

        Return the msg_id.
        """
        payload = MsgPayload(target_eid=target_eid, content=content, radius=radius)
        with self.__msg_outbox_lock:
            self.msg_outbox.append(payload)
        return payload.msg_id

    def msg_send_ensure(
        self, target_eid: int, content: str, radius: float
    ):
        """Send the tick every until sent successfully."""
        payload = MsgPayload(
            target_eid=target_eid,
            content=content,
            radius=radius,
            result=MsgStatus.ENSURE,
        )
        with self.__msg_outbox_lock:
            self.msg_outbox.append(payload)
        return payload.msg_id

    @classmethod
    def msg_target_has_inbox(cls, target: Character) -> TypeGuard[Type[MsgInboxMixin]]:
        """Check target character has inbox"""
        return hasattr(target, "msg_inbox")

    def msg_tick(self, belong: World) -> None:
        with self.__msg_outbox_lock:
            for p in self.msg_outbox:
                p.try_times += 1
                if p.result is MsgStatus.PENDING:
                    """Case PENDING"""
                    if belong.get_entity(
                        eid=p.target_eid
                    ):  # Entity in World.entity_dict is always a Character
                        """Check target exists silent"""
                        dis = belong._get_natural_distance(p.target_eid, self)

                        if dis is None:
                            p.status_update(MsgStatus.NOT_FOUND)
                            return

                        if dis <= p.radius:
                            """Only send msg in radius"""
                            target = belong.entity_dict[p.target_eid]
                            if self.msg_target_has_inbox(target):  # duck type
                                target.msg_inbox.append(p.content)
                                p.status_update(MsgStatus.SENT)
                            else:
                                p.status_update(MsgStatus.NO_INBOX)
                        else:
                            p.status_update(MsgStatus.NOT_FOUND)
                    else:
                        p.status_update(MsgStatus.NOT_FOUND)
                elif p.result is MsgStatus.ENSURE:
                    """Case ENSURE"""
                    if belong.get_entity(eid=p.target_eid):
                        dis = belong._get_natural_distance(p.target_eid, self)
                        if dis:
                            if dis <= p.radius:
                                target = belong.entity_dict[p.target_eid]
                                if self.msg_target_has_inbox(target):
                                    target.msg_inbox.append(p.content)
                                    # Only this case would set status to sentnt
                                    p.status_update(MsgStatus.SENT)
                    return
