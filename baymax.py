#!/usr/bin/python
# -*- coding:utf-8 -*-
import logging
import os
import signal

from core import const 
from core.brain import Brain 
from core.mic import Mic 

class Baymax(object):

    def __init__(self):
        self.mic = Mic()
        self.brain = Brain(self.mic)
        self.interrupted = False
       	logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s',
                datefmt='%Y%m%d %H:%M:%S',
                filename=const.log_file,
                filemode='w')
        # capture SIGINT signal, e.g., Ctrl+C
        signal.signal(signal.SIGINT, self.signal_handler)
     
    def signal_handler(self, signal, frame):
        self.interrupted = True
    
    def run(self):
        logging.info('Hello. I am Baymax, your personal companion.')
        self.mic.play(os.path.join(const.resources_path, "welcome.mp3"))
        while True:
            if self.interrupted:
                logging.info("Balalalala")
                break
	    detect = self.mic.detecting()
	    if detect == None:
                continue
            text = self.mic.listening()
            self.brain.determine(text)

if __name__ == "__main__":
    Baymax().run()
