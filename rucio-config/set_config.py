from rucio.client.configclient import ConfigClient
import sys, getopt, pprint

opts, args = getopt.getopt(sys.argv[1:], "s:")
opts = dict(opts)
section = opts["-s"]

name, value = args

client = ConfigClient(account="root")
client.set_config_option(section, name, value)
cfg = client.get_config(section)
pprint.pprint(cfg)
