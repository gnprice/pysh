from collections import namedtuple
import io
from typing import Any, Callable, List


def pipe_by_stream(left: 'Filter', right: 'Filter'):
    # TODO this exhausts left, then starts right.
    # This is where we really need async.
    def piped(input, output):
        buf = io.BytesIO()
        left.thunk(input, buf)
        buf.seek(0)
        return right.thunk(buf, output)
    return piped


class Filter:
    input: str   # 'none' | 'stream' | 'iter' | ...
    output: str  # 'none' | 'stream' | 'iter' | ...
    thunk: Callable[[Any, Any], None]

    def __init__(self, input, output, thunk):
        self.input = input
        self.output = output
        self.thunk = thunk

    def __iter__(self):
        if self.input != 'none' or self.output != 'iter':
            raise RuntimeError()
        return self.thunk(None, None)

    def __or__(self, other: 'Filter'):
        '''Aka `|` -- the pipe operator.'''
        if self.output != other.input:
            raise RuntimeError()
        if self.output == 'none':
            raise RuntimeError()
        elif self.output == 'stream':
            thunk = pipe_by_stream(self, other)
        elif self.output == 'iter':
            raise NotImplementedError()
        else:
            assert False
        return Filter(self.input, other.output, thunk)


Argspec = namedtuple('Argspec', ['type', 'n'])


class Function:
    '''A "shell function".'''

    func: Callable
    input: str   # 'none' | 'stream' | ...
    output: str  # 'none' | 'stream' | ...
    argspecs: List[Argspec]

    def __init__(self, func):
        self.func = func
        self.input = getattr(func, 'input', 'none')
        self.output = getattr(func, 'output', 'none')
        self.argspecs = getattr(func, 'argspecs', [])

    def __call__(self, *args, **kwargs):
        pass_input = (self.input == 'stream')
        pass_output = (self.output == 'stream')
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
        func.output = type
        return func
    return decorate


def input(*, type, required=True):
    def decorate(func):
        func.input = type
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
