import asyncio
from pyppeteer import launch

# from asgiref.sync import async_to_sync # HOF


class GameDriverPyppeteer():
    def __init__(self):
        def _patch_pyppeteer():
            from typing import Any
            from pyppeteer import connection, launcher
            import websockets.client

            class PatchedConnection(connection.Connection):
                def __init__(self, *args: Any, **kwargs: Any) -> None:
                    super().__init__(*args, **kwargs)
                    self._ws = websockets.client.connect(
                        self._url,
                        loop=self._loop,
                        max_size=None,
                        ping_interval=None,
                        ping_timeout=None,
                    )

            connection.Connection = PatchedConnection
            launcher.Connection = PatchedConnection
        _patch_pyppeteer()

        self.sensors = {}

    async def init_browser(self):
        self.browser = await launch(headless=False)
        self.page = await self.browser.newPage()  # redundant?
        self.client = await self.page.target().createCDPSession()

    async def add_sensor(self, name, sensor):
        if(name not in self.sensors):
            self.sensors[name] = sensor
            await sensor.install(self)
        return self.sensors

    async def remove_sensor(self, name):
        if(name in self.sensors):
            await self.sensors[name].remove(self)
            self.sensors.pop(name)
        return self.sensors

    def navigate(self, url):
        return async_run(self.page.goto(url))

    async def pause(self):
        return await self.send('Emulation.setVirtualTimePolicy', policy='pause')

    async def send(self, *args, **kwargs):
        if("evaluate" in args[0]):
            return await self.page.evaluate(kwargs["expression"], force_expr=True)
        elif("type" in args[0]):
            return await self.page.type(kwargs["target"], kwargs["expression"])
        else:
            return await self.client.send(*args, **kwargs)

    async def step(self):
        return {name: await sensor.observe(self) for name, sensor in self.sensors.items()}

    def close(self):
        async_run(self.browser.close())

    def __del__(self):
        self.close()


def async_run(func):
    asyncio.run_coroutine_threadsafe(func, asyncio.get_event_loop())
