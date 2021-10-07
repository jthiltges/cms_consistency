import yaml, sys, getopt
from rucio.client.rseclient import RSEClient
from rucio.common.exception import RSENotFound


CONFIG_SECTION_PREFIX = "consistency_enforcement"


Usage = """
python import_cc_config.py [-c] <config.yaml>

    -c      - create RSE if does not exist

"""


opts, args = getopt.getopt(sys.argv[1:], "c")
if not args:
    print(Usage)
    sys.exit(2)
    
opts = dict(opts)
create_rse = "-c" in opts
    
client = RSEClient()
    
cc_cfg = yaml.load(open(args[0], "r"), Loader=yaml.SafeLoader)
for rse, rse_cfg in cc_cfg["rses"].items():
    if rse == "*":
        continue
    try:
        client.get_rse(rse)
    except RSENotFound:
        if create_rse:
            client.add_rse(rse)
            print(f"New RSE {rse} created")
        else:
            print(f"RSE {rse} does not exist - skipping")
            continue
    attrs = client.list_rse_attributes()
    for k, v in rse_cfg.get("scanner", {}).items():
        k = CONFIG_SECTION_PREFIX + ".scanner." + k
        if k in attrs:
            client.delete_rse_attribute(rse, k)
        client.set_rse_attribute(rse, k, v)


