from IPython.display import display, clear_output, Image
from base64 import b64decode
from json import loads
from time import sleep
from random import choice
from abc import ABC, abstractmethod

class GameDriver():
    def __init__(self, cdp):
        self.cdp = cdp
        targetId = self.cdp.send('Target.createTarget',url='http://ipchicken.com',enableBeginFrameControl=True)['targetId']
        sessionId = self.cdp.send('Target.attachToTarget',targetId=targetId,flatten=True)['sessionId']
        
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
            self.navigate(self.cdp.send("Runtime.evaluate", expression="document.getElementsByTagName('iframe')[0].src")["result"]["value"])
        self.inject_event_script()
        return nav_output

    def inject_event_script(self):
        collection_script = '''(() => {
        let events = [];
        const inputs = (key, e) => [key, key.startsWith('mouse') ? [e.clientX, e.clientY, e.button] : String.fromCharCode(e.keyCode)];
        ['mousedown', 'mousemove', 'mouseup', 'keyup', 'keydown'].forEach(k => window.addEventListener(k, e => events.push({event: inputs(k,e), time: +new Date()}),true));
        window._getRecentEvents = () => events.splice(0, events.length);
        })();'''
        self.cdp.send("Runtime.evaluate", expression=collection_script)
        
    def get_browser_version(self):
        return self.cdp.send('Browser.getVersion')
    
    def pause(self):
        return self.cdp.send('Emulation.setVirtualTimePolicy', policy='pause')

    def step(self, actions=[], dur = None):
        for a in actions:
            a.apply(self)
        
        if dur is not None:
            for i in range(dur):
                self.cdp.send('HeadlessExperimental.beginFrame')
                self.cdp.send('Emulation.setVirtualTimePolicy', policy='advance', budget=1000/60)
        return {name: sensor.observe(self) for name,sensor in self.sensors.items()}
    
    def get_events(self):
        res = self.cdp.send("Runtime.evaluate", expression='JSON.stringify(window._getRecentEvents());')
        return loads(res['result']['value']) 
    
    def press_key(self, key):
        def text(letter):
            self.cdp.send("Input.dispatchKeyEvent", type="keyDown", windowsVirtualKeyCode=ord(letter), nativeVirtualKeyCode=ord(letter), key=letter)
            self.cdp.send("Input.dispatchKeyEvent", type="char", text= letter, key= letter)
            self.cdp.send("Input.dispatchKeyEvent", type="keyUp", windowsVirtualKeyCode=ord(letter), nativeVirtualKeyCode=ord(letter), key= letter)

        def ascii(char):
            self.cdp.send("Input.dispatchKeyEvent", type="keyDown", windowsVirtualKeyCode=ord(char), nativeVirtualKeyCode=ord(char), key=char)
            self.cdp.send("Input.dispatchKeyEvent", type="keyUp", windowsVirtualKeyCode=ord(char), nativeVirtualKeyCode=ord(char), key=char)
            
        success = False
        if(key.isalnum() or key is " "):
            if(len(key)==1):
                text(key)
            else:
                for k in key:
                    text(k)
            success = True
        elif(key.isascii()):
            if(len(key)==1):
                ascii(key)
            else:
                for k in key:
                    ascii(k)
            success=True
            
        return success
    
    def press_mouse(self, pos, button = 0, type="Moved"):
        buttons = ["left", "middle", "right"]
        return self.cdp.send('Input.dispatchMouseEvent', type="mouse" + type, x=pos["x"], y=pos["y"], button=buttons[button])
        
    def get_screenshot(self):
        res = self.cdp.send('HeadlessExperimental.beginFrame', screenshot={'format':'jpeg'})#, noDisplayUpdates=True)
#         res = self.cdp.send("Page.captureScreenshot")
#         print(res)
        if 'screenshotData' in res:
            clear_output()
            display(Image(b64decode(res['screenshotData'])))
        return res
    
    def run(self):
        self.event_log = [] 
        self.event_keys = [] 
        self.event_mouse = []
        read_mode = True
        print("record mode on")
        exit = False
        while not exit:
            if read_mode:
                for e in self.get_events():
        #             print(e)
                    if e['event'][0] == "keydown" and ord(e['event'][1]) == 220:
                        print("record mode off, playback mode on")
                        self.event_keys = [key["event"][1] for key in filter(lambda x: "keydown" in x["event"][0], self.event_log)]
                        self.event_log = []
                        read_mode = False
                        with open("keys.out", 'w') as log:
                            log.write(("_").join(self.event_keys))
                        break
                    elif e['event'][0] == "keydown" and ord(e['event'][1]) == 221:
                        self.event_log = []
                        print("clearing event log")
                        break
                    elif e['event'][0] == "keydown" and ord(e['event'][1]) == 219:
                        exit = True
                        print("exiting")
                        break
                    else:
                        self.event_log.append(e)
            else:
                with open('keys.out' , 'r') as log:
                    e_k = log.read()
                    self.event_keys = e_k.split("_")
                if(not self.event_keys):
                    read_mode = True
                    print("playback mode off, record mode on")
                    continue
        #         time.sleep(.1)
                e = choice(self.event_keys)
                self.press_key(e)
        #         print("pressed '"+e+"'")
                last = (lambda x: x[-1] if x else None)(self.get_events())
                if last and last['event'][0] == "keyup" and ord(last['event'][1]) == 220:
                    print("playback mode off, record mode on")
                    read_mode = True
                    self.event_keys = []
    
    def close(self):
        self.cdp.close()
        print("game driver closed")
        
    def send(self, *args, **kwargs):
        return self.cdp.send(*args, **kwargs)
    
    def __del__(self):
        self.close()
        
class Sensor(ABC):
    
    @abstractmethod
    def install(self, driver):
        pass
    
    @abstractmethod
    def observe(self, driver):
        pass
    
    @abstractmethod
    def remove(self, driver):
        pass
    
class Action(ABC):
    
    @abstractmethod
    def apply(self, driver):
        pass