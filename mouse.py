from game_driver import Action, Sensor
from json import loads


class MouseAction(Action):
    def __init__(self, mousetype, x, y, button):
        self.x = x
        self.y = y
        self.mousetype = mousetype
        self.buttoncode = button
        self.button = ["left", "middle", "right"][button]

    async def apply(self, driver):
        return await driver.send("Input.dispatchMouseEvent",
                                 type=self.mousetype,
                                 x=self.x,
                                 y=self.y,
                                 button=self.button)

    def __repr__(self):
        return str({"pos": (self.x, self.y), "button": str(self.button) + "("+str(self.buttoncode)+")", "mousetype": self.mousetype})


class MouseSensor(Sensor):
    async def install(self, driver):
        mouse_script = '''
        let mouseEvents = [];
        let mouseSensorInstallDate = +new Date();
        ['mouseup', 'mousemove', 'mousedown'].forEach(m =>
            window.addEventListener(m, 
                e => mouseEvents.push({
                    event: m, 
                    x: e.clientX,
                    y: e.clientY,
                    button: e.button,
                    time: +new Date() - mouseSensorInstallDate
                }), 
            true)
        );
        window._getMouseEvents = () => mouseEvents.splice(0, mouseEvents.length);
        '''
        return await driver.send("Runtime.evaluate", expression=mouse_script)

    async def observe(self, driver):
        res = await driver.send("Runtime.evaluate", expression="JSON.stringify(window._getMouseEvents());")
        try:
            mouses = loads(res['result']['value'])
        except:
            mouses = loads(res)
        mouse_actions = [(m['time'], MouseAction(
            m["event"], m["x"], m["y"], m["button"])) for m in mouses]
        return mouse_actions

    async def remove(self, driver):
        remove_mouse = '''['mouseup', 'mousemove', 'mousedown'].forEach(m => window.removeEventListener(m, true));'''
        return await driver.send("Runtime.evaluate", expression=remove_mouse)
