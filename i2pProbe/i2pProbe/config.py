import yaml

CONFIG = {}

DEFAULT_CONFIG = {
    "onions": [],  # this is ignored but used by the freeweb exporter service to configure onionprobe
    "eepsites": [],  # this is where se store eepistes: [ "myeepsite.b32.i2p", "myeepsite2.b32.i2p" ]
}


def load_config(filename):
    global CONFIG
    with open(filename) as fh:
        CONFIG = yaml.safe_load(fh.read())


def get_config():
    global CONFIG
    return CONFIG
