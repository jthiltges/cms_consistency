from rucio.client.configclient import ConfigClient
import sys, pprint

Usage = """
python print_config.py <section>
"""

if not sys.argv[1:]:
    print(Usage)
    sys.exit(2)
    
section = sys.argv[1]

client = ConfigClient(account="root")
cfg = client.print_config(section)
pprint.pprint(cfg)
