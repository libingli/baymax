# -*- coding:utf-8 -*-
import base64
import collections
import const
import datetime
import hmac
import hashlib
import json
import logging
import os
import pyaudio
import requests
import sys
import time
import urllib2
from urlparse import urlparse
import wave

reload(sys)  
sys.setdefaultencoding('utf-8') 
sys.path.append("..")
from snowboy import snowboydetect 

class Snowboy(object):
    """
    Snowboy decoder to detect whether a keyword specified by `decoder_model`
    exists in a microphone input stream.

    :param decoder_model: decoder model file path, a string or a list of strings
    :param resource: resource file path.
    :param sensitivity: decoder sensitivity, a float of a list of floats.
                              The bigger the value, the more senstive the
                              decoder. If an empty list is provided, then the
                              default sensitivity in the model will be used.
    :param audio_gain: multiply input volume by this factor.
    """
    def __init__(self, hotword, 
    		 decoder_model,
                 resource=os.path.join(const.resources_path, "common.res"),
                 sensitivity=[],
                 audio_gain=1):

        self.logger = logging.getLogger("snowboy")

        def audio_callback(in_data, frame_count, time_info, status):
            self.ring_buffer.extend(in_data)
            play_data = chr(0) * len(in_data)
            return play_data, pyaudio.paContinue

        tm = type(decoder_model)
        ts = type(sensitivity)
        if tm is not list:
            decoder_model = [decoder_model]
        if ts is not list:
            sensitivity = [sensitivity]
        model_str = ",".join(decoder_model)

        self.detector = snowboydetect.SnowboyDetect(
            resource_filename=resource.encode(), model_str=model_str.encode())
        self.detector.SetAudioGain(audio_gain)
        self.num_hotwords = self.detector.NumHotwords()

        if len(decoder_model) > 1 and len(sensitivity) == 1:
            sensitivity = sensitivity*self.num_hotwords
        if len(sensitivity) != 0:
            assert self.num_hotwords == len(sensitivity), \
                "number of hotwords in decoder_model (%d) and sensitivity " \
                "(%d) does not match" % (self.num_hotwords, len(sensitivity))
        sensitivity_str = ",".join([str(t) for t in sensitivity])
        if len(sensitivity) != 0:
            self.detector.SetSensitivity(sensitivity_str.encode())

        size = self.detector.NumChannels() * self.detector.SampleRate() * 5
        self.ring_buffer = collections.deque(maxlen=size)
        self.audio = pyaudio.PyAudio()
        self.stream_in = self.audio.open(
            input=True, output=False,
            format=self.audio.get_format_from_width(
                self.detector.BitsPerSample() / 8),
            channels=self.detector.NumChannels(),
            rate=self.detector.SampleRate(),
            frames_per_buffer=2048,
            stream_callback=audio_callback)
	self.hotword = hotword


    def detecting(self, sleep_time=0.03):
        """
        Start the voice detector. For every `sleep_time` second it checks the
        audio buffer for triggering keywords. 
        :param float sleep_time: how much time in second every loop waits.
        :return: None
        """
        #self.logger.debug("detecting...")

        data = bytes(bytearray(self.ring_buffer))
        self.ring_buffer.clear()
	if len(data) == 0:
	    time.sleep(sleep_time)
	    return None 

	ans = self.detector.RunDetection(data)
	if ans == -1:
	    self.logger.warning("Error initializing streams or reading audio data")
	    return None 
	elif ans > 0:
	    message = "Hi. I am " + str(self.hotword) + ", may I help you"
	    self.logger.info(message)
            return self.hotword

    def terminate(self):
        """
        Terminate audio stream. Users cannot call start() again to detect.
        :return: None
        """
        self.stream_in.stop_stream()
        self.stream_in.close()
        self.audio.terminate()

ak_id = const.config["Alibaba"]["ak_id"]
ak_secret = const.config["Alibaba"]["ak_secret"]

def get_current_date():
    date = datetime.datetime.strftime(datetime.datetime.utcnow(), "%a, %d %b %Y %H:%M:%S GMT")
    return date

def to_md5_base64(body):
    hash = hashlib.md5()
    hash.update(body)
    m = hash.digest().encode('base64').strip()
    hash = hashlib.md5()
    hash.update(m)
    return hash.digest().encode('base64').strip()

def to_sha1_base64(stringToSign, secret):
    hmacsha1 = hmac.new(secret, stringToSign, hashlib.sha1)
    return base64.b64encode(hmacsha1.digest())

# TODO
def transcribe(fp):
    try:
        wav_file = wave.open(fp, 'rb')
    except IOError:
        return []

    n_frames = wav_file.getnframes()
    frame_rate = wav_file.getframerate()
    audio = wav_file.readframes(n_frames)
    date = datetime.datetime.strftime(datetime.datetime.utcnow(),
                                      "%a, %d %b %Y %H:%M:%S GMT")
    options = {
        'url': 'https://nlsapi.aliyun.com/recognize?model=chat',
        'method': 'POST',
        'body': audio,
    }
    headers = {
        'authorization': '',
        #'content-type': 'audio/wav; samplerate=%s' % str(frame_rate),
        'content-type': 'audio/wav', 
        'accept': 'application/json',
        'date': date,
        'Content-Length': str(len(audio))
    }

    body = ''
    if 'body' in options:
        body = options['body']

    bodymd5 = ''
    if not body == '':
        bodymd5 = to_md5_base64(body)

    stringToSign = options['method'] + '\n' + \
        headers['accept'] + '\n' + bodymd5 + '\n' + \
        headers['content-type'] + '\n' + headers['date']
    signature = to_sha1_base64(stringToSign, ak_secret)

    authHeader = 'Dataplus ' + ak_id + ':' + signature
    headers['authorization'] = authHeader
    url = options['url']
    requests.packages.urllib3.disable_warnings()
    r = requests.post(url, data=body, headers=headers, verify=False)
    try:
        text = ''
	if 'result' in r.json():
	    text = r.json()['result'].encode('utf-8')
    except requests.exceptions.HTTPError:
        logging.error("HTTPError")
        return []
    except requests.exceptions.RequestException:
        logging.error("RequestException")
        return []
    except ValueError as e:
        logging.error("ValueError", e)
        return []
    except KeyError:
        logging.error("KeyError")
        return []
    else:
        transcribed = []
        if text:
            transcribed.append(text)
	logging.info('阿里云语音识别到了: %s' % text)
        return text 

if __name__ == "__main__":
    print transcribe(os.path.join(const.resources_path, "welcome.mp3"))
