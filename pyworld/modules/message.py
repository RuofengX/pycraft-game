from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import List, TypeGuard

from objprint import op  # type:ignore

from pyworld.world import Character, Entity, World

# TODO: Use Metaclass to regulate those generate of Mixin module.


class DebugMixin:
    """For those needs"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__DEBUG_FLAG = True

    def _debug_tick(self, belong=Entity):
        op(self)
        op(belong)


class MsgInboxMixin(Character):
    """MsgInboxMixin provides a basic inbox function and a static status enum.

    An entity could inherit this mixin to gain the ability for receiving msg.
    Or, like a duck type, if an entity have msg_inbox property, it could receive msg.

    A entity whit MsgInbox must have an position, or msg sent to it will always failure.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.msg_inbox: List[bytes] = []


class MsgStatus(Enum):
    """Enum of MsgStatus"""

    PENDING = "Msg is in outbox and waiting for next msg_tick."
    SENT = "Msg is successfully sent to target."
    NO_INBOX = "Target is found in send-radius, \
        but target does not have property msg_inbox."
    NOT_FOUND = "Target is not found in send radius. Ensure your target_id is correct."
    ENSURE = "Msg is marked as ensure, will always try to send at every tick, \
        until set to SENT."


@dataclass(eq=False)
class MsgPayload:
    """MsgPayload is the entry of  msg.outbox list
    it contains some necessary info about the message it self.
    """

    target_eid: int  # Receiver of the message
    content: bytes  # Content of the message
    radius: float  # Broadcast radius
    result: MsgStatus = MsgStatus.PENDING  # The send status set by MsgMixin
    try_times: int = field(
        default=0, init=False
    )  # Send times, it is helpful for ENSURE message
    msg_id: int = field(init=False)  # Msg ID, which is an UUID4().int

    def __post_init__(self):
        self.msg_id = uuid.uuid4().int

    def status_update(self, status: MsgStatus):
        self.result = status

    def __hash__(self) -> int:
        return self.msg_id

    def __eq__(self, other: object) -> bool:
        if isinstance(other, MsgPayload):
            return self.msg_id == other.msg_id
        else:
            return False


class MsgMixin(MsgInboxMixin, Character):
    """MsgMixin is a module provided basic message of an entity.

    Like a visible-light shape of a thing in real world.

    It provides a basic level control of send & receive msg.
    Extra limits and restricts should be implemented on higher level class.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.msg_outbox: List[MsgPayload] = []
        self.msg_radius: float = 100.0

    def __static_init__(self):
        self.__msg_outbox_lock = Lock()
        super().__static_init__()

    def msg_send(self, target_eid: int, content: bytes) -> int:
        """Send message to other entity with target_eid,
        target entity must have msg_mixin.

        Message will be limited in msg_radius.

        Return the msg_id.
        """
        payload = MsgPayload(
            target_eid=target_eid, content=content, radius=self.msg_radius
        )
        with self.__msg_outbox_lock:
            self.msg_outbox.append(payload)
        return payload.msg_id

    def msg_send_ensure(self, target_eid: int, content: bytes):
        """Send the msg every tick until sent successfully."""
        payload = MsgPayload(
            target_eid=target_eid,
            content=content,
            radius=self.msg_radius,
            result=MsgStatus.ENSURE,
        )
        with self.__msg_outbox_lock:
            self.msg_outbox.append(payload)
        return payload.msg_id

    @classmethod
    def _msg_target_has_inbox(cls, target: Entity) -> TypeGuard[MsgInboxMixin]:
        """Check target character has inbox"""
        return hasattr(target, "msg_inbox")

    def _msg_tick(self, belong: World) -> None:
        """Automatically send messages from outbox to target.inbox"""
        with self.__msg_outbox_lock:
            for p in self.msg_outbox:
                p.try_times += 1
                if p.result is MsgStatus.PENDING:
                    """Case PENDING"""
                    if belong.world_get_entity(
                        eid=p.target_eid
                    ):  # Entity in World.entity_dict is always a Character
                        """Check target exists silent"""
                        dis = belong.world_get_natural_distance(p.target_eid, self)

                        if dis is None:
                            p.status_update(MsgStatus.NOT_FOUND)
                            return

                        if dis <= p.radius:
                            """Only send msg in radius"""
                            target: Entity = belong.entity_dict[p.target_eid]
                            if self._msg_target_has_inbox(target):  # duck type
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
                    if belong.world_get_entity(eid=p.target_eid):
                        dis = belong.world_get_natural_distance(p.target_eid, self)
                        if dis:
                            if dis <= p.radius:
                                target = belong.entity_dict[p.target_eid]
                                if self._msg_target_has_inbox(target):
                                    target.msg_inbox.append(p.content)
                                    # Only this case would set status to sent
                                    p.status_update(MsgStatus.SENT)
                    return
