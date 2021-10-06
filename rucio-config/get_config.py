from rucio.client.configclient import ConfigClient
import sys, getopt, pprint

opts, args = getopt.getopt(sys.argv[1:], "s:")
opts = dict(opts)
section = opts.get("-s")

client = ConfigClient(account="root")
cfg = client.get_config(section)
pprint.pprint(cfg)
