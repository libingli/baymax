# -*- coding: utf-8-*-
import logging
import json
import requests
import sys

sys.path.append("..")
from core import const
from core.mic import Mic 
from uuid import getnode 

reload(sys)
sys.setdefaultencoding('utf-8')

turing_key = const.config['Turing']['apikey'] 
 
def handle(text, mic=None):
    if text == "":
        mic.say("你说什么", "pardon.mp3")
        return
    msg = ''.join(text)
    try:
        url = const.config['Turing']['openapi'] 
        userid = str(getnode())[:32]
        body = {'key': turing_key, 'info': msg, 'userid': userid}
        r = requests.post(url, data=body)
	respond = json.loads(r.text)
        answer = ''
        if respond['code'] == 100000:
            answer = r.json()['text'].encode('utf-8')
        elif respond['code'] == 200000:
            answer = respond['url']
        elif respond['code'] == 302000:
            for k in respond['list']:
                answer = answer + u"【" + k['source'] + u"】 " + k['article'] + "\t" + k['detailurl'] + "\n"
        else:
            answer = respond['text'].replace('<br>', '  ')
            answer = answer.replace(u'\xa0', u' ')
        mic.say(answer, "chat.mp3")
    except Exception as e:
        logging.error("Turing robot failed to responsed for %r, %s", msg, e)
        answer = "抱歉, 我的大脑短路了, 请稍后再试试."
        mic.say(answer, "chat_error.mp3")
    return 

if __name__ == "__main__":
    handle("现在几点了", Mic())
