import asyncio
import inspect


async def nested(msg):
    print(f"{msg}...")
    await asyncio.sleep(1)
    print(f"{msg} done.")

async def demo_main():
    nested(42)
    await nested(99)
    # await t


async def for_la(input, body):
    async for line in input:
        words = line.split()
        if inspect.isasyncgenfunction(body):
            async for out in body(words):
                yield out
        else:
            for out in body(words):
                yield out

async def demo_for_la():
    async def input():
        for line in ['yes 1', 'no', 'yes 2 3']:
            yield line
            await asyncio.sleep(0.3)
    async def body(words):
        if words[0] == 'yes':
            for x in words[1:]:
                yield x
    async for line in for_la(input(), body):
        print(line)
    async for line in for_la(input(),
            lambda words: (x for x in words[1:] if words[0] == 'yes')):
        print(line)


async def for_iter(input, body):
    return await body(input)

async def demo_for_iter():
    async def input():
        for line in ['1', '2', '3']:
            yield line
            await asyncio.sleep(0.01)
    async def body(input):
        # TODO this sure would be convenient to somehow allow:
        # return sum(int(l) for l in input)
        tot = 0
        async for l in input:
            tot += int(l)
        return tot
    print(await for_iter(input(), body))


async def demo_subprocess():
    proc = await asyncio.create_subprocess_exec(
        *['sh', '-c', 'echo yes 1; sleep 0.3; echo yes 2 3'],
        stdout=asyncio.subprocess.PIPE)
    async def body(words):
        yield words[1]
    async for line in for_la(proc.stdout, body):
        print(line)

asyncio.run(demo_subprocess())
