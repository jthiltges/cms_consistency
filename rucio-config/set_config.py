from rucio.client.configclient import ConfigClient
import sys, pprint

Usage = """
python set_config <section> <name> <value>
"""

if len(sys.argv[1:]) != 3:
    print(Usage)
    sys.exit(2)

section, name, value = sys.argv[1:]

client = ConfigClient(account="root")
client.set_config_option(section, name, value)
cfg = client.get_config(section)
pprint.pprint(cfg)
