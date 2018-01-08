# -*- coding: utf-8-*-
# 网易云音乐播放插件
import logging
import threading
import hashlib
import time
import subprocess
import sys
import os
import re
import random

sys.path.append("..")
from musicbox.api import NetEase
from musicbox.player import Player
from utils import const

reload(sys)
sys.setdefaultencoding('utf8')

class MusicBox(object):

    def __init__(self, mic):
        self.username = const.config["Netease"]["username"] 
        self.password = const.config["Netease"]["password"] 
	self.userid = ""
        self.mic = mic
        self.player = Player()
        #self.player.playing_song_changed_callback = self.song_changed_callback
        self.netease = NetEase()
        self.exit = False
        self.logger = logging.getLogger(__name__)
        self.login()

    def login(self):
        self.logger.info("正在为您登录网易云音乐")
        password = hashlib.md5(self.password).hexdigest()
	user_info = self.netease.login(self.username, password)
	if user_info['code'] != 200:
	    self.mic.say("网易云音乐登录失败, 请检查配置后再试", "music_login_error.mp3")
            return -1
        self.logger.info("登录成功")
        self.userid = user_info['account']['id']

    # 每日推荐
    def recommend(self):
        idx = 0
        datatype = 'songs'
        title = '每日推荐'
        myplaylist = self.netease.recommend_playlist()
        if myplaylist == -1:
            return
        datalist = self.netease.dig_info(myplaylist, datatype)
        
        self.player.new_player_list('songs', title, datalist, -1)
        self.player.end_callback = None
        self.player.play_and_pause(idx)

    def favorite(self):
        idx = 0
        datatype = 'top_playlists'
        title = '我的歌单'
        myplaylist = self.netease.user_playlist(self.userid)
        if myplaylist == -1:
            return
        datalist = self.netease.dig_info(myplaylist, datatype)
            
        playlist_id = datalist[idx]['playlist_id']
        songs = self.netease.playlist_detail(playlist_id)
        datatype = 'songs'
        datalist = self.netease.dig_info(songs, datatype)
        
        self.player.new_player_list('songs', title, datalist, -1)
        self.player.end_callback = None
        self.player.play_and_pause(idx)
   
    def options(self, command):
        if any(ext in command for ext in [u"结束", u"退出", u"停止"]):
            self.player.stop()
            self.exit = True
	    self.mic.say("结束音乐播放", "music_stop.mp3")
        elif u'随机' in command:
            self.player.info['playing_mode'] = 3
            self.player.next()
        elif any(ext in command for ext in [u'下一首', u"下首歌", 
            u"切歌", u"下一首歌", u"换首歌", u"切割", u"那首歌"]):
            self.player.next()
        elif any(ext in command for ext in [u'喜欢']):
            self.netease.fm_like(self.player.get_playing_id())
	    self.mic.say("操作成功", "success.mp3")
            self.player.resume()
        elif any(ext in command for ext in [u'我的', u"歌单"]):
            self.favorite()
        elif any(ext in command for ext in [u'推荐']):
            self.recommend()
        elif any(ext in command for ext in [u"大音量", u"大点声", u"大声点"]):
            self.player.volume_up()
            self.player.resume()
        elif any(ext in command for ext in [u"小音量", u"小点声", u"小声点"]):
            self.player.volume_down()
            self.player.resume()
        elif u'什么' in command:
            answer = "正在播放的是%s的<%s>" % (self.player.playing_artist, self.player.playing_name)
            self.mic.say(answer) 
            self.player.resume()
        else:
            self.mic.say("你说什么,如果使用其他技能请先结束音乐播放", "music_pardon.mp3")

    def start(self):
        self.recommend()
	while True:
            if self.exit:
                return

            transcribed = self.mic.detecting(sleep_time=0.3)
            if not transcribed:
                continue

            # 当听到呼叫机器人名字时，停止播放
            self.player.pause()
            command = self.mic.listening()
            self.options(command)

# Standard module stuff
WORDS = ["MUSIC"]

def handle(text, mic):
    """
    Responds to user-input, typically speech text
    Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
    """
    # single 
    logging.info("Starting music mode")
    music = MusicBox(mic)
    music.start()
    return

def isValid(text):
    """
        Returns True if the input is related to music.
        Arguments:
        text -- user-input, typically transcribed speech
    """
    return any(word in text for word in [u"听歌", u"音乐", u"我想听", u"唱歌", u"唱首歌"])
