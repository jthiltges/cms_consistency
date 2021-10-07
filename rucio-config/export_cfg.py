from rucio.client.configclient import ConfigClient
import sys, getopt, pprint
from configparser import ConfigParser

opts, args = getopt.getopt(sys.argv[1:], "s:")
opts = dict(opts)
root = opts.get("-s")

client = ConfigClient()
all_sections = client.get_config()

cfg = ConfigParser()

for section, section_cfg in data.items():
    if root and (section == root or section.startswith(root+".")):
        cfg.add_section(section)
        for k, v in section_cfg.items():	
        	cfg.set(section, k, str(v))
cfg.write(sys.stdout)
