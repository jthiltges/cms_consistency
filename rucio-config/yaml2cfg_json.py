#
# Convert CC YAML config file into the combination of .cfg file with RSE defaults 
# and .json file for each RSE with RSE-specific configuration
#

import sys, getopt, os, yaml, json
from configparser import ConfigParser

def copy_config(config_in, field, config_out, section, default=None, required=True):
    if field not in config_in and required:
        raise KeyError(f"Rquired field {field} not found")
    value = config_in.get(field, default)
    if value is not None:
        config_out.set(section, field, str(value))

Usage = """
python yaml2cfg_json.py <config.yaml> <output_directory>
"""

if len(sys.argv[1:]) != 2:
    print(Usage)
    sys.exit(2)

config_file, out_dir = sys.argv[1:]
config_in = yaml.load(open(config_file, "r"), Loader=yaml.SafeLoader).get("rses",{})
defaults_in = config_in.get("*", {})

os.makedirs(out_dir, exist_ok=True)
    
cp = ConfigParser()
cp.add_section("consistency_enforcement")
cp.add_section("consistency_enforcement.scanner")
cp.add_section("consistency_enforcement.dbdump")

cp.set("consistency_enforcement", "npartitions", str(defaults_in.get("partitions", 10)))

if "scanner" in defaults_in:
    scanner_in = defaults_in["scanner"]
    
    copy_config(scanner_in, "recursion", cp, "consistency_enforcement.scanner")
    copy_config(scanner_in, "nworkers", cp, "consistency_enforcement.scanner", 10)
    copy_config(scanner_in, "timeout", cp, "consistency_enforcement.scanner", 60)
    copy_config(scanner_in, "server_root", cp, "consistency_enforcement.scanner", required = True)
    copy_config(scanner_in, "remove_prefix", cp, "consistency_enforcement.scanner", "/")
    copy_config(scanner_in, "add_prefix", cp, "consistency_enforcement.scanner", "/")
    
    #print("scanner_in:", scanner_in)
    roots_in = scanner_in.get("roots")
    #print("roots_in:", roots_in)
    root_paths = [r["path"] for r in roots_in]
    cp.set("consistency_enforcement.scanner", "roots", " ".join(root_paths))
    
    for r in roots_in:
        path = r["path"]
        ignore = r.get("ignore")
        if ignore:
            cp.add_section(f"consistency_enforcement.scanner.root.{path}")
            cp.set(f"consistency_enforcement.scanner.root.{path}", "ignore", " ".join(ignore))
    
if "dbdump" in defaults_in:
    dbdump_in = defaults_in["dbdump"]
    cp.set("consistency_enforcement.dbdump", "path_root", dbdump_in["path_root"])
    if "ignore" in dbdump_in:
        ignore = dbdump_in["ignore"]
        cp.set("consistency_enforcement.dbdump", "ignore", " ".join(ignore))
        
cp.write(open(out_dir + "/common.cfg", "w"))

for rse, rse_config in config_in.items():
    if rse == "*":  continue
    #print(f"RSE {rse} config:")
    #print(rse_config)
    with open(out_dir + f"/{rse}.json", "w") as out:
        json.dump(rse_config, out)

    
