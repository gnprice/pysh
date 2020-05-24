'''
If we're autodoc'ing a callable with a ``__signature__``, use it.

The built-in behavior of autodoc *almost* gets this right.
It mostly delegates to `inspect.signature` to find the signature,
and that in turn looks for a ``__signature__`` attribute and
uses that as the signature, if any.  Which is essential for,
e.g., decorators that add or remove parameters.

Unfortunately autodoc doesn't leave enough up to `inspect`.  In
particular, before calling `inspect.signature` it looks for a
`__call__` attribute, and if it finds one (and the object doesn't fall
into some other categories) it calls `inspect.signature` on *that*,
instead of on the object itself.  See the implementation of
`FunctionDocumenter.format_args` in sphinx/ext/autodoc/__init__.py .

Fortunately there's enough customizability built in, and in particular
a hook event emitted just before that `inspect.signature` call, that
we can work around this from a further Sphinx extension.  Here it is.

TODO: get this fixed upstream :-)
  (Looks to be https://github.com/sphinx-doc/sphinx/issues/7613 .)
'''

import types


def fix_signature(app, obj, bound_method):
    if not isinstance(obj, types.MethodType) or obj.__name__ != '__call__':
        # In the case we're working around here, the `obj` passed in
        # this event will be a method named __call__.  This one isn't.
        return

    if not hasattr(obj.__self__, '__signature__'):
        # Self-object has no __signature__ anyway, so nothing to do.
        return

    if hasattr(obj, '__signature__'):
        # The method itself has a __signature__ -- let that govern.
        return

    # We'd like to say:
    #   obj.__signature__ = obj.__self__.__signature__
    #
    # (Well, that'd still be awkward, but it'd be as clean as a
    # workaround for this autodoc issue can probably get.)
    #
    # But that fails because `obj` is a (bound) method and we can't give
    # it a `__signature__` attribute -- trying raises AttributeError.
    #
    # Instead, take advantage of the fact that the next line in the
    # autodoc implementation is going to re-look-up the __call__:
    #
    #   # from FunctionDocumenter.format_args
    #   # at sphinx/ext/autodoc/__init__.py:1032-1034 as of Sphinx v3.0.3
    #     self.env.app.emit('autodoc-before-process-signature',
    #                       unwrapped.__call__, False)
    #     sig = inspect.signature(unwrapped.__call__)
    #
    # and just mutate `unwrapped` itself, i.e. obj.__self__.
    #
    # TODO maybe something fancier, like a wrapper function?  This
    #   version is fine as long as the interpreter running Sphinx
    #   never tries to actually *call* the callable...
    obj.__self__.__call__ = obj.__self__


def setup(app):
    app.connect('autodoc-before-process-signature', fix_signature)

    return dict(
        version='0.1',
        parallel_read_safe=True,
        parallel_write_safe=True,
    )
