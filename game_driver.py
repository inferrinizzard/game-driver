from IPython.display import display, clear_output, Image
from base64 import b64decode
from abc import ABC, abstractmethod
from time import sleep


class GameDriver():
    def __init__(self, cdp):
        self.cdp = cdp
        targetId = self.cdp.send(
            'Target.createTarget', url='http://ipchicken.com', enableBeginFrameControl=True)['targetId']
        sessionId = self.cdp.send(
            'Target.attachToTarget', targetId=targetId, flatten=True)['sessionId']
        self.sensors = {}

    def add_sensor(self, name, sensor):
        if(name not in self.sensors):
            self.sensors[name] = sensor
            sensor.install(self)
        return self.sensors

    def remove_sensor(self, name):
        if(name in self.sensors):
            self.sensors[name].remove(self)
            self.sensors.pop(name)
        return self.sensors

    def navigate(self, address):
        nav_output = self.cdp.send('Page.navigate', url=address)
        if 'itch.io' in address:
            sleep(1)
            self.navigate(self.cdp.send(
                "Runtime.evaluate", expression="document.getElementsByTagName('iframe')[0].src")["result"]["value"])
        return nav_output

    def get_browser_version(self):
        return self.cdp.send('Browser.getVersion')

    def pause(self):
        return self.cdp.send('Emulation.setVirtualTimePolicy', policy='pause')

    def step(self, actions=[], dur=None, screenshot=False, log=False):
        for a in actions:
            a.apply(self)

        if dur is not None:
            for i in range(dur):
                self.cdp.send('HeadlessExperimental.beginFrame')
                self.cdp.send('Emulation.setVirtualTimePolicy',
                              policy='advance', budget=1000/60)
        # sensor.observe(self, name+".out")
        return {name: sensor.observe(self) for name, sensor in self.sensors.items() if screenshot or 'screen' not in name}

    def close(self):
        self.cdp.close()
        for sensor in [k for k in self.sensors.keys()]:
            self.remove_sensor(sensor)
        print("game driver closed")

    def send(self, *args, **kwargs):
        return self.cdp.send(*args, **kwargs)

    def __del__(self):
        self.close()


class Sensor(ABC):

    def install(self, driver):
        pass

    @abstractmethod
    def observe(self, driver):
        pass

    def remove(self, driver):
        pass


class Action(ABC):

    @abstractmethod
    def apply(self, driver):
        pass
