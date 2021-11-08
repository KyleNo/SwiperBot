#https://stackoverflow.com/questions/45419723/python-timer-with-asyncio-coroutine

import asyncio

class Timer:
    def __init__(self, timeout, callback, args):
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job(args))

    async def _job(self, args):
        await asyncio.sleep(self._timeout)
        await self._callback(*args)

    def cancel(self):
        self._task.cancel()
