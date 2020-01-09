from game_driver import Action, Sensor
from json import loads


class KeyboardAction(Action):

    # constructor accepts key (string) and eventtype (event type)
    def __init__(self, eventtype, key):
        self.eventtype = eventtype
        self.keycode = ord(key)
        self.key = key

    # sends emulated action to driver
    async def apply(self, driver):  # try force run?
        return await driver.send("Input.dispatchKeyEvent",
                                 type=self.eventtype,
                                 windowsVirtualKeyCode=self.keycode,
                                 nativeVirtualKeyCode=self.keycode,
                                 key=self.key)

    # returns dict of key, key code and event type on string
    def __repr__(self):
        return str({"key": self.key, "keycode": self.keycode, "eventtype": self.eventtype})


class KeyboardSensor(Sensor):
    async def install(self, driver):
        keyboard_script = '''
        let keyEvents = [];
        let keySensorInstallDate = +new Date();
        ['keyup', 'keydown'].forEach(k =>
            window.addEventListener(k, 
                e => keyEvents.push({
                    event: k, 
                    key: String.fromCharCode(e.keyCode),
                    time: +new Date() - keySensorInstallDate
                }), 
            true)
        );
        window._getKeyboardEvents = () => keyEvents.splice(0, keyEvents.length);
        '''
        return await driver.send("Runtime.evaluate", expression=keyboard_script)

    async def observe(self, driver):
        res = await driver.send(
            "Runtime.evaluate", expression="JSON.stringify(window._getKeyboardEvents());")
        try:
            keys = loads(res['result']['value'])
        except:
            keys = loads(res)
        keyboard_actions = [(k['time'], KeyboardAction(
            k["event"], k["key"])) for k in keys]
        return keyboard_actions

    async def remove(self, driver):
        remove_keyboard = '''['keyup', 'keydown'].forEach(k => window.removeEventListener(k, true));'''
        return await driver.send("Runtime.evaluate", expression=remove_keyboard)
