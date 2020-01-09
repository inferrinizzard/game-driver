from game_driver import Sensor

class CodeCoverage(Sensor):

    def observe(self, driver):
        return driver.send("Profiler.getBestEffortCoverage")["result"]
        