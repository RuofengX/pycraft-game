# Mixin modules

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

