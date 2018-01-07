#!/usr/bin/python
# -*- coding:utf-8 -*-
''' mic.py
play MP3 music files using Python module pygame
pygame is free from: http://www.pygame.org
(does not create a GUI frame in this case)
'''
import audioop
import logging
import os
import pyaudio
import pygame 
import tempfile
import time
import tts
import wave

import const
import stt

class Mic:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.stop_passive = False 
	model = os.path.join(const.resources_path, "baymax.pmdl")
	self.snowboy = stt.Snowboy("Baymax", model, sensitivity=0.5)
    
    def __del__(self):
        self.snowboy.terminate()

    def getScore(self, data):
        rms = audioop.rms(data, 2)
        score = rms / 3
        return score

    def detecting(self, sleep_time=0.03):
	detect = self.snowboy.detecting(sleep_time)
        if detect != None:
            self.play_wave(os.path.join(const.resources_path, "ding.wav")) 
        return detect

    def listening(self):
        """
        Listens for PERSONA in everyday sound. Times out after LISTEN_TIME, so
        needs to be restarted.
        """

        THRESHOLD_MULTIPLIER = 2.5
        RATE = 16000
        CHUNK = 1024

        # number of seconds to allow to establish threshold
        THRESHOLD_TIME = 1

        # number of seconds to listen before forcing restart
        LISTEN_TIME = 10

        # prepare recording stream
	_audio = pyaudio.PyAudio()
        stream = _audio.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=RATE,
                                  input=True,
                                  frames_per_buffer=CHUNK)

        # stores the audio data
        frames = []

        # stores the lastN score values
        lastN = [i for i in range(30)]

        didDetect = False

        # calculate the long run average, and thereby the proper threshold
        for i in range(0, RATE / CHUNK * THRESHOLD_TIME):

            try:
                if self.stop_passive:
                    break

                data = stream.read(CHUNK)
                frames.append(data)

                # save this data point as a score
                lastN.pop(0)
                lastN.append(self.getScore(data))
                average = sum(lastN) / len(lastN)

                # this will be the benchmark to cause a disturbance over!
                THRESHOLD = average * THRESHOLD_MULTIPLIER

                # save some memory for sound data
                frames = []

                # flag raised when sound disturbance detected
                didDetect = False
            except Exception, e:
                self.logger.error(e)
                pass

        # start passively listening for disturbance above threshold
        for i in range(0, RATE / CHUNK * LISTEN_TIME):

            try:
                if self.stop_passive:
                    break

                data = stream.read(CHUNK)
                frames.append(data)
                score = self.getScore(data)

                if score > THRESHOLD:
                    didDetect = True
                    break
            except Exception, e:
                self.logger.error(e)
                continue

        # no use continuing if no flag raised
        if not didDetect:
            self.logger.info("没接收到唤醒指令")
            try:
                # self.stop_passive = False
                stream.stop_stream()
                stream.close()
            except Exception, e:
                self.logger.error(e)
                pass
            return None

        # cutoff any recording before this disturbance was detected
        frames = frames[-20:]

        # otherwise, let's keep recording for few seconds and save the file
        DELAY_MULTIPLIER = 1
        for i in range(0, RATE / CHUNK * DELAY_MULTIPLIER):

            try:
                if self.stop_passive:
                    break
                data = stream.read(CHUNK)
                frames.append(data)
            except Exception, e:
                self.logger.error(e)
                continue

        # save the audio data
        try:
            # self.stop_passive = False
            stream.stop_stream()
            stream.close()
        except Exception, e:
            self.logger.error(e)
            pass

        with tempfile.NamedTemporaryFile(mode='w+b') as f:
            wav_fp = wave.open(f, 'wb')
            wav_fp.setnchannels(1)
            wav_fp.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
            wav_fp.setframerate(RATE)
            wav_fp.writeframes(''.join(frames))
            wav_fp.close()
            f.seek(0)
            frames = []
            # check if PERSONA was said
            transcribed = stt.transcribe(f)

        return transcribed


    def play(self, audio_file, volume=0.8):
        '''
        stream music with mixer.music module in a blocking manner
        this will stream the sound from disk while playing
        '''
        # set up the mixer
        freq = 15500 # audio CD quality
        bitsize = -16    # unsigned 16 bit
        channels = 2     # 1 is mono, 2 is stereo
        buffer = 2048    # number of samples (experiment to get best sound)
        pygame.mixer.init(freq, bitsize, channels, buffer)
        pygame.mixer.init()
        # volume value 0.0 to 1.0
        pygame.mixer.music.set_volume(volume)
        clock = pygame.time.Clock()
        try:
            pygame.mixer.music.load(audio_file)
            self.logger.debug("Music file {} loaded".format(audio_file))
        except pygame.error:
            self.logger.error("File {} not found ({})".format(audio_file, pygame.get_error()))
            return
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            # check if playback has finished
            clock.tick(30)

    def play_wave(self, fname):
        """Simple callback function to play a wave file. By default it plays
        a Ding sound.

        :param str fname: wave file name
        :return: None
        """
        fd = wave.open(fname, 'rb')
        data = fd.readframes(fd.getnframes())
        audio = pyaudio.PyAudio()
        stream_out = audio.open(
            format=audio.get_format_from_width(fd.getsampwidth()),
            channels=fd.getnchannels(),
            rate=fd.getframerate(), input=False, output=True)
        stream_out.start_stream()
        stream_out.write(data)
        time.sleep(0.2)
        stream_out.stop_stream()
        stream_out.close()
        audio.terminate()

    def say(self, text, file_name=os.path.join(const.resources_path, "chat.mp3")):
    	self.logger.info(text)
        mp3 = tts.send_request(text)
        fd = open(file_name, "w+")
        fd.write(mp3)
        fd.close()
        volume = 1.0 
        self.play(file_name, volume)

# pick a MP3 music file you have in the working folder
# otherwise give the full file path
if __name__ == "__main__":
    audio_file = os.path.join(const.resources_path, "welcome.mp3")
    # optional volume 0 to 1.0
    volume = 1.0 
    mic = Mic()
    mic.play(audio_file, volume)
    mic.say("稍等，正在为您登录网易云音乐")
