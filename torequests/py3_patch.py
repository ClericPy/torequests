# here for python3 patch avoid of python2 SyntaxError
import asyncio

def new_future_await(self):
    loop = asyncio.get_event_loop()
    future = loop.run_in_executor(None, self.result, self._timeout)
    for i in future:
        yield i
    return self.x