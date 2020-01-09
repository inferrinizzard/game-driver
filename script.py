from game_driver import Sensor

class Script(Sensor):
    def __init__(self, expression):
        self.expression = expression
        
    def observe(self, driver):
        return driver.send("Runtime.evaluate",expression=self.expression)["result"]