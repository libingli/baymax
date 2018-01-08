# encoding: UTF-8
import os
import yaml

work_path = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), os.pardir))
conf_path = os.path.join(work_path, 'config')
resources_path = os.path.join(work_path, 'resources')
log_path = os.path.join(work_path, 'log')

log_file = os.path.join(log_path, 'baymax.log')
config = yaml.load(file(os.path.join(work_path, 'config/baymax.yaml'), 'r'))
print (config)

music_config = os.path.join(conf_path, 'music.json')
music_cache = os.path.join(log_path, 'music_cache')
music_storage = os.path.join(log_path, 'music_storage.json')
music_cookie = os.path.join(log_path, 'cookie')
