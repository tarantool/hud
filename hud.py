#!/usr/bin/env python3

import gevent
from gevent import monkey
monkey.patch_all()

from gevent.wsgi import WSGIServer
import flask
from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
from flask_bootstrap import Bootstrap

import os
import sys
import logging
import yaml
import importlib
import argparse

script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(script_dir, 'sensors'))

import concourse
import travis
import packagecloud

app = Flask(__name__)
app.config['DEBUG'] = True
Bootstrap(app)

MODULES = []

def get_config(config_file):
    cfg = {}
    if config_file:
        with open(config_file, 'r') as stream:
            try:
                cfg = yaml.load(stream)
            except yaml.YAMLError as exc:
                print("Failed to parse config file:\n" + str(exc))
                sys.exit(1)

    return cfg

@app.route('/')
def root():
    modules = []
    for module in MODULES:
        modules.append({'name': module['module_name'],
                        'data': module['module'].get(module['cfg'])})

    return flask.render_template('main.html',
                                 modules = modules)


def update_fiber(module_name, module, cfg):
    while True:
        try:
            logging.info("Updating data of %s" % module_name)
            module.update(cfg)
            logging.info("Updated data of %s" % module_name)
        except ex:
            logging.exception("Failed to update data of %s" % module_name)
        gevent.sleep(module.UPDATE_INTERVAL_SECONDS)

def main():
    logging.getLogger("requests").setLevel(logging.WARNING)

    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', default='config.yml')

    args = parser.parse_args()


    cfg = get_config(args.config)

    modules = []
    for module_name in os.listdir(os.path.join(script_dir, 'sensors')):
        if module_name.endswith('.py'):
            module_name = module_name[:-3]
            modules.append({'module_name': module_name,
                            'module': importlib.import_module(module_name),
                            'cfg': cfg[module_name]})
    global MODULES
    MODULES = modules

    for module in modules:
        gevent.spawn(update_fiber,
                     module['module_name'],
                     module['module'],
                     module['cfg'])


    listen_port = 8080
    http_server = WSGIServer(('', listen_port), app)
    logging.info("Listening on port %d", listen_port)
    http_server.serve_forever()


if __name__ == '__main__':
    main()
