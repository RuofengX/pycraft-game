# Mixin modules

## Implements multiple functions for entities in the pycraft

Every being or entity have their own property or method,
but some of these functions are same. So we write those same
reuseable function as some mixin modules.
Each mixin class act as a set of ports, like Interface in Java.

## Name regulation

Mixin modules named as `<Name>Mixin`,
variables named as `<module_name>_<variable_name>`,
methods named as `<module_name>_<method_name>`,
If a mixin module needs some public type or utils, write it as a separate mixin,
and name them as `<Name><Util_name>`. Also notice that only mixin class would
be inherit to the final entity type.

For example:

```python

    class MsgPayload():
        ...


    class MsgMixin(Character):
        def __init__(self):
            self.msg_inbox = []

        def msg_send(self):
            ...

```

## The `_tick` method

Entity instance will run every method named after '_tick' in every tick.

The '_tick' method must have two positional arguments, which is:

1. instance itself, also know as `self`;
2. (Optional)the belonging of this instance. In most case is the Continuum instance.

`_tick` function return None.

## Inherit order

Entity instance will initiate mixin classes first, then the entity class, which will solve most of teh MRU problems.
For example, an entity instance with MsgMixin and Character should wrote in these:
`class CharacterWithMsgMixin(MsgMixin, Character)`

If a mixin module(class) is only available to some specific entity type, inherit it,
like `class MsgMixin(Character)` means that MsgMixin could only apply to the type
of `Character`.

## Serialization and Persistence

Pyworld uses pickle module to save all of the object.
But some types is not supported by pickle.
As a resolution, every property that cannot be serialized by pickle module should be masked with a _ mark before, like `_<property_name>`. Property with protect mark `__<property_name>` is also recognized as Non-Pickle-able property.

Every entity has a `__getstate__` and `__setstate__` method, which will properly del those `_<property_name>`. Thus, for those object that couldn't be pickled, e.g. `threading.Lock()`, there are a special method to initiate and 're-setstate' when load from an binary save file.

Entity has an `__static_init__` method, which will recreate those non-pickled properties which were thrown by `__getstate__`.
The `__static_init__` method would be called automatically in `Entity().__init__()` method, and will also be called in `Entity().__setstate__()` method when the object is restore from pickle bytes.
Any override `__static_init__` method should run `super().__static_init__()` so that other mixin property could initiate correctly.

### TL;DR

All you need to do is: If any of property in the mixin module cannot be pickled, make sure they are stateless and write those init method in `__static_init__`, not in `__init__`; Also make sure your `__init__` and `__static_init__` methods has called `super().__static_init__()`.

Also, json serialize would use `__getstate__` method, and no reference cycle is allowed in Entity type.

## Exception Handle

Only handle exceptions in Mixin class, in lower class or data model, raise them.
All the exceptions should be handled in entity layer.
