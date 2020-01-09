from game_driver import Action, Sensor
from IPython.display import display, clear_output, Image
from base64 import b64decode
class Screenshot():
    def __init__(self, image):
        self.image = image
        
    def display(self):
        clear_output()
        display(Image(b64decode(self.image)))
        
class ScreenSensor(Sensor):
    def install(self, driver):
        pass
        
    def observe(self, driver, image_format='jpeg', quality=1):
#         res = driver.send('Page.captureScreenshot', format=image_format, **({} if image_format == 'jpeg' else {"quality":quality}))
#         if('data' in res):
#             return Screenshot(res['data'])
        try:
            res = driver.send('Page.captureScreenshot', format=image_format, **({} if image_format == 'jpeg' else {"quality":quality}))
            if('data' in res):
                return Screenshot(res['data'])
            return res
        except Exception as e:
            print("could not take screenshot")
            print(e)
        finally:
            return None
        
    def remove(self, driver):
        pass
    