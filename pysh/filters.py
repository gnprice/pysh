from collections import namedtuple
import io
from typing import Any, Callable, List, NamedTuple


def pipe_by_stream(left: 'Filter', right: 'Filter'):
    # TODO this exhausts left, then starts right.
    # This is where we really need async.
    def piped(input, output):
        buf = io.BytesIO()
        left.thunk(input, buf)
        buf.seek(0)
        return right.thunk(buf, output)
    return piped


class IoSpec(NamedTuple):
    type: str = 'none'  # 'none' | 'stream' | 'iter' | 'bytes' | ...
    required: bool = True


class Filter:
    input: IoSpec
    output: IoSpec
    thunk: Callable[[Any, Any], None]

    def __init__(self, input, output, thunk):
        self.input = input
        self.output = output
        self.thunk = thunk

    def __call__(self):
        if self.input.required and self.input.type != 'none':
            raise RuntimeError()
        if (self.output.type in ('none', 'iter', 'bytes')
              or not self.output.required):
            return self.thunk(None, None)
        elif self.output.type == 'stream':
            raise NotImplementedError()  # Return the pipe/stream.
        else:
            assert False

    def __iter__(self):
        if self.output.type != 'iter':
            raise RuntimeError()
        return self()

    def __or__(self, other: 'Filter'):
        '''Aka `|` -- the pipe operator.'''
        if self.output.type != other.input.type:
            raise RuntimeError()
        if self.output.type == 'none':
            raise RuntimeError()
        elif self.output.type == 'stream':
            thunk = pipe_by_stream(self, other)
        elif self.output.type == 'iter':
            raise NotImplementedError()
        else:
            assert False
        return Filter(self.input, other.output, thunk)


Argspec = namedtuple('Argspec', ['type', 'n'])


class Function:
    '''A "shell function".'''

    func: Callable
    input: IoSpec
    output: IoSpec
    argspecs: List[Argspec]

    def __init__(self, func):
        self.func = func
        self.input = getattr(func, 'input', IoSpec())
        self.output = getattr(func, 'output', IoSpec())
        self.argspecs = getattr(func, 'argspecs', [])

    def __call__(self, *args, **kwargs):
        pass_input = (self.input.type == 'stream')
        pass_output = (self.output.type == 'stream')
        if pass_input and pass_output:
            thunk = (lambda input, output:
                     self.func(input, output, *args, **kwargs))
        elif pass_input:
            thunk = lambda input, _: self.func(input, *args, **kwargs)
        elif pass_output:
            thunk = lambda _, output: self.func(output, *args, **kwargs)
        else:
            thunk = lambda: self.func(*args, **kwargs)
        return Filter(self.input, self.output, thunk)


def filter(func):
    return Function(func)


def output(*, type, required=True):
    def decorate(func):
        func.output = IoSpec(type, required)
        return func
    return decorate


def input(*, type, required=True):
    def decorate(func):
        func.input = IoSpec(type, required)
        return func
    return decorate


def argument(*, type='string', n=1):
    # Not really implemented.
    def decorate(func):
        if not hasattr(func, 'argspecs'):
            func.argspecs = []
        func.argspecs.append(Argspec(
            type=type, n=n,
        ))
        return func
    return decorate


def option(*names, type):
    # Not actually implemented.
    def decorate(func):
        return func
    return decorate
