import yaml, re, os, configparser

from rucio.client.configclient import ConfigClient
from rucio.client.rseclient import RSEClient
from rucio.common.exception import ConfigNotFound

CONFIG_SECTION_PREFIX = "consistency_enforcement"

class DBConfig:

	# class to read relevant parameters from rucio.cfg

    def __init__(self, schema, dburl):
        self.DBURL = dburl
        self.Schema = schema
    
    @staticmethod
    def from_cfg(path):
        cfg = configparser.ConfigParser()
        cfg.read(path)
        dbparams = dict(cfg.items("database"))
        return DBConfig(dbparams.get("schema"), dbparams["default"])
        
    @staticmethod
    def from_yaml(path_or_dict):
        if isinstance(path_or_dict, str):
            cfg = yaml.load(open(path_or_dict, "r"), Loader=yaml.SafeLoader)["database"]
        else:
            cfg = path_or_dict

        user = cfg["user"]
        password = cfg["password"]
        schema = cfg["schema"]
        conn_str = None
        if "connstr" in cfg:
            conn_str = cfg["connstr"]
            dburl = "oracle+cx_oracle://%s:%s@%s" % (user, password, conn_str)
        else:
            host = cfg["host"]
            port = cfg["port"]
            service = cfg["service"]
            dburl = "oracle+cx_oracle://%s:%s@%s:%s/?service_name=%s" % (
                                    user, password, host, port, service)
        return DBConfig(schema, dburl)
        
class DefaultsConfig(BaseConfig):
    """
    roots = express mc data generator results hidata himc relval
    recursion = 1
    nworkers = 8
    timeout = 300
    server_root = /store/
    remove_prefix = /
    add_prefix = /store/
    include_sizes = yes

    """
    
    def __init__(self):

        config_client = ConfigClient()

        cfg = config_client.get_config(CONFIG_SECTION_PREFIX)
        self.IgnoreList = [x.strip() for x in cfg.get("ignore","").split()]
        self.IgnoreList = [x for x in self.IgnoreList if x]
        self.NPartitions = int(cfg.get("npartitions", 5))

        cfg = config_client.get_config(CONFIG_SECTION_PREFIX + ".scanner")
        self.ServerRoot = cfg.get("server_root", "/store/")
        self.ScannerTimeout = int(cfg.get("timeout", 300))
        self.RootList = [x.strip() for x in cfg.get("roots","").split()]
        self.RootList = [x for x in self.RootList if x]
        self.RemovePrefix = cfg.get("remove_prefix", "/")
        self.AddPrefix = cfg.get("add_prefix", "/store/")
        self.NWorkers = int(cfg.get("nworkers", 8))
        self.IncludeSizes = cfg.get("include_sizes", "yes") == "yes"
        self.RecursionThreshold = int(cfg.get("recursion", 1))
        
        cfg = config_client.get_config(CONFIG_SECTION_PREFIX + ".db_dump")
        self.DBDumpPathRoot = cfg.get("path_root", "/")
            
    def get_root(self, root):
        return self.RootConfigs[root]
        
class CombinedRSEConfig(BaseConfig):
    
    def __init__(self, defaults, rse):
        self.__dict__.update(defaults.__dict__)     # copy defaults
        cfg = RSEClient().list_rse_attributes(rse)
        self.ServerURL = cfg[CONFIG_SECTION_PREFIX + ".scanner.server"]
        self.ServerRoot = cfg.get(CONFIG_SECTION_PREFIX + ".scanner.server_root", 
            self.ServerRoot)
        self.IncludeSizes = cfg.get(CONFIG_SECTION_PREFIX + ".scanner.include_sizes",
            self.IncludeSizes)
        self.ScannerTimeout = cfg.get(CONFIG_SECTION_PREFIX + ".scanner.timeout", 
            self.ScannerTimeout)
        root_list = cfg.get(CONFIG_SECTION_PREFIX + ".scanner.roots")
        if root_list:
            root_list = [r.strip() for r in root_list.split() if r.strip()]
            self.RootList = root_list

Defaults = DefaultsConfig()
RSE_Configs = {}

def rse_config(rse):
    global RSE_Configs
    c = RSE_Configs.get(rse)
    if c is None:
        c = RSE_Configs[rse] = CombinedRSEConfig(Defaults, rse)
    return c
    
def core_config():
    return Defaults
