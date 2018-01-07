#!/usr/bin/python
# -*- coding:utf-8 -*-
import base64
import const
import datetime
import hmac
import hashlib
import json
import logging
import urllib2
from urlparse import urlparse

def get_current_date():
    date = datetime.datetime.strftime(datetime.datetime.utcnow(), "%a, %d %b %Y %H:%M:%S GMT")
    return date

def to_md5_base64(body):
    hash = hashlib.md5()
    hash.update(body)
    return hash.digest().encode('base64').strip()

def to_sha1_base64(stringToSign, secret):
    hmacsha1 = hmac.new(secret, stringToSign, hashlib.sha1)
    return base64.b64encode(hmacsha1.digest())

def authorization(method, body, accept,content_type, date, ak_id, ak_secret):
    # 1.对body进行MD5+BASE64加密
    bodymd5 = ''
    if not body == '':
        bodymd5 = to_md5_base64(body)

    # 2.特征值
    # 这里和标准方法的区别主要在于拼接特征值时不需要urlpath。
    stringToSign = method + '\n' + accept + '\n' + bodymd5 + '\n' + content_type + '\n' + date

    signature = to_sha1_base64(stringToSign, ak_secret)

    # Authorization: Dataplus access_id:signature
    authHeader = 'Dataplus ' + ak_id + ':' + signature
    return authHeader

def send_request(body):
    ak_id = const.config["Alibaba"]["ak_id"]
    ak_secret = const.config["Alibaba"]["ak_secret"]
    method = "POST"
    url = 'https://nlsapi.aliyun.com/speak?encode_type=mp3&&volume=50'
    content_type = 'text/plain'
    accept = 'audio/wav, application/json'
    date = get_current_date()
    auth = authorization(method, body, accept, content_type, date, ak_id, ak_secret)
    options = {
        'url': url,
        'method': method,
        'body': body,
        'headers': {
            'accept': accept,
            'content-type': content_type,
            'date':  date,
            'authorization': auth
        }
    }

    request = None
    if 'GET' == method or 'DELETE' == method:
        request = urllib2.Request(url)
    elif 'POST' == method or 'PUT' == method:
        request = urllib2.Request(url, body)
    request.get_method = lambda: method

    for key, value in options['headers'].items():
        request.add_header(key, value)

    try:
        conn = urllib2.urlopen(request)
        response = conn.read()
        return response
    except urllib2.HTTPError, e:
        logging.error(e.read())
        raise SystemExit(e)

if __name__ == "__main__":
    text = "今天天气：晴,白天温度5度,晚上温度-6度,西北风3-4级"
    print send_request(text)
