# -*- coding: utf-8-*-
import logging
import json
import requests
import sys

sys.path.append("..")
from utils import const
from utils.mic import Mic 
from uuid import getnode 

reload(sys)
sys.setdefaultencoding('utf-8')

tuling_key = const.config['Turing']['apikey'] 
 
def handle(text, mic=None):
    if text == "":
        mic.say("你说什么？")
        return
    msg = ''.join(text)
    try:
        url = const.config['Turing']['openapi'] 
        userid = str(getnode())[:32]
        body = {'key': tuling_key, 'info': msg, 'userid': userid}
        r = requests.post(url, data=body)
	respond = json.loads(r.text)
        result = ''
        if respond['code'] == 100000:
            result = r.json()['text'].encode('utf-8')
        elif respond['code'] == 200000:
            result = respond['url']
        elif respond['code'] == 302000:
            for k in respond['list']:
                result = result + u"【" + k['source'] + u"】 " + k['article'] + "\t" + k['detailurl'] + "\n"
        else:
            result = respond['text'].replace('<br>', '  ')
            result = result.replace(u'\xa0', u' ')
    except Exception as e:
        logging.error("Tuling robot failed to responsed for %r, %s", msg, e)
        result = "抱歉, 我的大脑短路了, 请稍后再试试."
    mic.say(result)
    return 

if __name__ == "__main__":
    handle("现在几点了", Mic())
