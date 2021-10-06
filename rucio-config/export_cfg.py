from rucio.client.configclient import ConfigClient
import sys, getopt, pprint
from configparser import ConfigParser

opts, args = getopt.getopt(sys.argv[1:], "s:")
opts = dict(opts)
section = opts.get("-s")

client = ConfigClient()
data = client.get_config(section)

cfg = ConfigParser()
cfg.add_section(section)
for k, v in data.items():
	
	cfg.set(section, k, str(v))
cfg.write(sys.stdout)
