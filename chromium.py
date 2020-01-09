from subprocess import Popen, PIPE
from os import path
from psutil import Process

class Chromium():
    def __init__(self, port=None, headless=True, no_sandbox=True, surface_synchronisation=True, run_compositor_stages=True, disable_threaded_animation=True, disable_threaded_scrolling=True, disable_checker_imaging=True, disable_gpu=True):
        _remote_debugging_port = "--remote-debugging-port="+ str(port or 9222)
        _headless = "--headless" if headless else ""
#         _no_sandbox = "--no-sandbox" if no_sandbox else ""
        _no_sandbox = ""
        _surface_synchronisation = "--enable-surface-synchronization" if surface_synchronisation else ""
        _run_compositor_stages = "--run-all-compositor-stages-before-draw" if run_compositor_stages else ""
        _disable_threaded_animation = "--disable-threaded-animation" if disable_threaded_animation else ""
        _disable_threaded_scrolling = "--disable-threaded-scrolling" if disable_threaded_scrolling else ""
        _disable_checker_imaging = "--disable-checker-imaging" if disable_checker_imaging else ""
        _disable_gpu = "--disable-gpu" if disable_gpu else ""
        self.flags=[_remote_debugging_port, _headless, _no_sandbox, _surface_synchronisation, _run_compositor_stages, _disable_threaded_animation, _disable_threaded_scrolling, _disable_checker_imaging, _disable_gpu]
        args = (" ").join([flag for flag in self.flags if flag])
        
        if(path.isfile(".\\chrome-win\\chrome.exe")):
            self.chrome = Popen(".\\chrome-win\\chrome chromium-browser "+args, shell=True, stdout=PIPE, stderr=PIPE)
            print("chrome started")
        else:
            print("missing: chromium, please install from «https://www.chromium.org/getting-involved/download-chromium»")
            print('once installed, please extract folder "chrome-win" into current directory')
            
        output = ""
        lines = 0
        while "ws" not in output:
            output = str(self.chrome.stderr.readline())
            lines = lines+1
            if "error" in output or lines>100:
                break
        try:
            assert("ws" in output)
            self.url = output[output.index("ws"):-5]
            print("hosting at: " + self.url + "\n")
        except:
            print("did not read ws url properly")
            print("latest output: "+output)
            self.close()
        
    # autoclose with timer
    def close(self):
        try:
            process = Process(self.chrome.pid)
            for proc in process.children(recursive=True):
                proc.kill()
            process.kill()
            self.url = None
            print("chromium closed")
        except Exception as e:
            print("could not close chromium with exception: "+str(e))
        
    def __del__(self):
        self.close()
