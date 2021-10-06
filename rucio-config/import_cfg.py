from rucio.client.configclient import ConfigClient
import sys, getopt, pprint
from configparser import ConfigParser
from rucio.common.exception import ConfigNotFound

opts, args = getopt.getopt(sys.argv[1:], "s:")
opts = dict(opts)
section = opts.get("-s")
cfg = ConfigParser()
cfg_file = args[0]
if cfg_file == "-":
	cfg_file = sys.stdin
else:
	cfg_file = open(cfg_file, "r")
cfg.read_file(cfg_file)

if section:
	sections = [section]
else:
	sections = cfg.sections()

client = ConfigClient()
for s in sections:
	print(f"Importing [{s}]...")
	try:
		existing_data = client.get_config(s)
	except ConfigNotFound:
		print(f"new section [{s}]")
	else:
		for k in set(existing_data.keys()) - set(cfg.options(s)):
			print(f"Deleting key {k}")
	for k in cfg.options(s):
		v = cfg.get(s, k)
		print(f"Setting value for {k}: {v}")
		client.set_config_option(s, k, v)
