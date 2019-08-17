from collections import namedtuple
import io
import sys
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


def pipe_by_tstream(left: 'Filter', right: 'Filter'):
    # TODO this exhausts left, then starts right.
    # This is where we really need async.
    def piped(input, output):
        buf = io.StringIO()
        left.thunk(input, buf)
        buf.seek(0)
        return right.thunk(buf, output)
    return piped


class IoSpec(NamedTuple):
    type: str = 'none'  # 'none' | 'stream' | 'tstream' | 'iter' | 'bytes' | ...
    required_: bool = True

    @property
    def required(self) -> bool:
        return self.required_ and self.type != 'none'


class Filter:
    input: IoSpec
    output: IoSpec
    thunk: Callable[[Any, Any], None]

    def __init__(self, input, output, thunk):
        self.input = input
        self.output = output
        self.thunk = thunk

    def __call__(self):
        if self.input.required:
            raise RuntimeError()
        if self.output.required and Filter.pass_output(self.output):
            raise NotImplementedError()  # Probably return the pipe/stream.
        return self.thunk(None, None)

    def __iter__(self):
        if self.output.type in ('none', 'stream', 'tstream', 'bytes'):
            raise RuntimeError()
        assert self.output.type in ('iter',)
        return self()

    def __or__(self, other: 'Filter'):
        '''Aka `|` -- the pipe operator.'''
        if self.output.type != other.input.type:
            raise RuntimeError()
        if self.output.type in ('none',):
            raise RuntimeError()
        elif self.output.type in ('iter', 'bytes'):
            raise NotImplementedError()
        assert self.output.type in ('stream', 'tstream')

        if self.output.type == 'stream':
            thunk = pipe_by_stream(self, other)
        else:
            thunk = pipe_by_tstream(self, other)
        return Filter(self.input, other.output, thunk)


    @staticmethod
    def pass_input(input: IoSpec) -> bool:
        '''Whether the thunk expects input as an argument.'''
        if input.type in ('stream', 'tstream', 'iter', 'bytes'):
            return True
        elif input.type in ('none',):
            return False
        assert False

    @staticmethod
    def pass_output(output: IoSpec) -> bool:
        '''Whether the thunk expects output as an argument.'''
        if output.type in ('stream', 'tstream'):
            return True
        elif output.type in ('none', 'iter', 'bytes'):
            return False
        assert False


slurp_filter = Filter(IoSpec('stream'), IoSpec('bytes'),
                     lambda input, _: input.read().rstrip(b'\n'))

def slurp(filter):
    '''
    Run the pipeline and capture output, stripping any trailing newlines.

    Stripping trailing newlines is the same behavior as `$(...)` has
    in Bash.  It fits nicely with conventional semantics for Unix CLI tools.

    See also `pysh.subprocess.slurp_cmd`.
    '''
    # For reference on `$(...)` see Bash manual, 3.5.4 Command Substitution.
    return (filter | slurp_filter)()


def to_stdout(filter):
    '''
    Run the pipeline, with output directed to our stdout.
    '''
    if filter.input.required:
        raise RuntimeError()
    if filter.output.type in ('none', 'iter', 'bytes'):
        raise RuntimeError()
    assert filter.output.type in ('stream', 'tstream')
    if filter.output.type == 'stream':
        filter.thunk(None, sys.stdout.buffer)
    else:
        filter.thunk(None, sys.stdout)


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
        pass_input = Filter.pass_input(self.input)
        pass_output = Filter.pass_output(self.output)
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
