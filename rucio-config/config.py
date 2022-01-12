from __future__ import print_function
import yaml, re, os, json
from configparser import ConfigParser

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
        
class ConfigBackend(object):
    
    def get_config(self, rse="*"):
        raise NotImplementedError()
        
    def get_root_list(self, rse="*"):
        raise NotImplementedError()
        
    def get_root(self, root, rse_name="*"):
        raise NotImplementedError()

    def get_scanner(self, rse_name="*"):
        return self.get_config(rse_name).get("scanner", {})

    def get_top(self, rse_name="*"):
        return self.get_config(rse_name)

    def get_dbdump(self, rse_name="*"):
        return self.get_config(rse_name).get("dbdump", {})

    def get_value(self, name, specifc, common, default, required):
        if name in specifc:
            return specifc[name]
        if name in common:
            return common[name]
        if required:
            raise KeyError(f"Required field {name} not found")
        else:
            return default
            
    def section_as_dict(self, parser, section):
        out = {}
        for name, value in parser.items(section):
            try:    value = int(value)
            except: pass
            out[name] = value
        return out
        
    def roots_as_dict(self, iterable):
        return {r["path"]:r for r in iterable}

    def scanner_param(self, rse_name, param, default=None, required=False):
        # 1. rses->rse->param
        # 2. rses->*->param
        scanner_rse = self.get_scanner(rse_name)
        scanner_common = self.get_scanner()
        #print("scanner_rse:", scanner_rse)
        return self.get_value(param, scanner_rse, scanner_common, default, required)
        
    def format_ignore_list(self, lst):
        if not lst: lst = []
        if isinstance(lst, str):
            if " " in lst:
                lst = lst.split()
            else:
                lst = [lst]
        return lst
            
    def root_param(self, rse_name, root, param, default=None, required=False):
        # 1. rses->rse->root->param
        # 2. rses->*->root->param
        root_rse = self.get_root(root, rse_name) or {}
        root_common = self.get_root(root)
        value = self.get_value(param, root_rse, root_common, default, required)
        if param == "ignore": value = self.format_ignore_list(value)
        return value
            
    def dbdump_param(self, rse_name, param, default=None, required=False):
        # 1. rses->rse->param
        # 2. rses->*->param
        dbdump_rse = self.get_dbdump(rse_name)
        defaults = self.get_dbdump()
        value = self.get_value(param, dbdump_rse, defaults, default, required)
        if param == "ignore": value = self.format_ignore_list(value)
        return value

    def rse_param(self, rse_name, param, default=None, required=False):
        rse_cfg = self.get_top(rse_name)
        defaults = self.get_top()
        return self.get_value(param, rse_cfg, defaults, default, required)
        
class ConfigDictBackend(ConfigBackend):
    
    def __init__(self, cfg):
        if isinstance(cfg, str):
            cfg = yaml.load(open(cfg, "r"), Loader=yaml.SafeLoader)
        cfg = cfg.get("rses", {})
        self.Config = cfg
        self.Roots = {}             # {rse -> {root -> root_config}} 
        for rse, data in cfg.items():
            roots = data.get("scanner", {}).get("roots", [])
            self.Roots[rse] = self.roots_as_dict(roots)
        #print("ConfigDictBackend.Config:", self.Config)
        #print("ConfigDictBackend.__init__: Roots:", self.Roots)

    def get_config(self, rse="*"):
        cfg = self.Config.get(rse, {})
        #print(f"get_config({rse}): cfg:", cfg)
        return self.Config.get(rse, {})
        
    def get_root_list(self, rse="*"):
        return list(self.Roots.get(rse, {}).keys())
        
    def get_root(self, root, rse="*"):
        return self.Roots.get(rse, {}).get(root)

class ConfigFilesBackend(ConfigBackend):

    CONFIG_SECTION_PREFIX = "consistency_enforcement"
    
    def __init__(self, dirpath):
        import glob, json
        self.DirPath = dirpath
        defaults, default_roots = self.read_common(dirpath + "/common.cfg")

        self.Config = json.load(open(dirpath + "/specifics.json", "r"))
        self.Roots = {}

        for rse, rse_config in self.Config.items():
            self.Roots[rse] = self.roots_as_dict(rse_config.get("scanner", {}).get("roots", []))

        self.Config["*"] = defaults
        self.Roots["*"] = default_roots
    
    def read_common(self, path):
        cp = ConfigParser()
        cp.read_file(open(path, "r"))
        cfg = {}

        for section in cp.sections():
            section_data = self.section_as_dict(cp, section)
            if section == self.CONFIG_SECTION_PREFIX:
                cfg.update(section_data)
            elif section == self.CONFIG_SECTION_PREFIX + ".dbdump":
                cfg["dbdump"] = section_data
            elif section == self.CONFIG_SECTION_PREFIX + ".scanner":
                cfg["scanner"] = section_data
            elif section.startswith(self.CONFIG_SECTION_PREFIX + ".scanner.root."):
                pass
                
        root_paths = cfg.get("scanner", {}).get("roots", "").split()
        roots = {path:self.section_as_dict(cp, self.CONFIG_SECTION_PREFIX + ".scanner.root." + path) for path in root_paths}
        #print("read_common ->", cfg, roots)
        return cfg, roots
        
    def read_rse_specific(self, path):
        rse = path.rsplit("/", 1)[-1].split(".", 1)[0]
        cfg = json.load(open(path, "r"))
        roots = self.roots_as_dict(cfg.get("scanner", {}).get("roots", []))
        return rse, cfg, roots

    def get_config(self, rse="*"):
        return self.Config.get(rse, {})
        
    def get_root_list(self, rse="*"):
        return list(self.Roots.get(rse, {}).keys())
        
    def get_root(self, root, rse="*"):
        return self.Roots.get(rse, {}).get(root)


class ConfigRucioBackend(ConfigBackend):

    CONFIG_SECTION_PREFIX = "consistency_enforcement"

    def __init__(self, account="root"):
        from rucio.client.configclient import ConfigClient
        from rucio.client.rseclient import RSEClient
        from rucio.common.exception import ConfigNotFound

        self.RSEClient = RSEClient(account=account)
        self.ConfigClient = ConfigClient(account=account)
        
        self.Common = None
        self.CommonRoots = None

        self.RSESpecific = {}
        self.RSERoots = {}
        
    def get_config(self, rse="*"):
        if rse == "*":
            if self.Common is None:
                self.Common = self.ConfigClient.get_config(self.CONFIG_SECTION_PREFIX)
                scanner = self.Common["scanner"] = self.ConfigClient.get_config(self.CONFIG_SECTION_PREFIX + ".scanner")
                dbdump = self.Common["dbdump"] = self.ConfigClient.get_config(self.CONFIG_SECTION_PREFIX + ".dbdump")
            return self.Common
        else:
            cfg = self.RSESpecific.get(rse)
            if cfg is None:
                cfg = {}
                try:    cfg = self.RSEClient.list_rse_attributes(rse.upper())
                except: pass
                if cfg:
                    cfg = cfg.get(self.CONFIG_SECTION_PREFIX, "{}")
                    cfg = json.loads(cfg)
                self.RSESpecific[rse] = cfg
                self.RSERoots[rse] = self.roots_as_dict(cfg.get("scanner", {}).get("roots", []))
            return cfg
        
    def get_root_list(self, rse="*"):
        
        if rse == "*":
            return self.get_config(rse).get("scanner", {}).get("roots", "").split()
        else:
            cfg = self.get_config(rse)  # this will fetch self.RSERoots[rse] as dict
            return list(self.RSERoots.get(rse, {}).keys())
            
    def get_root(self, root, rse_name="*"):
        raise NotImplementedError()



if __name__ == "__main__":
    import sys, getopt
    opts, args = getopt.getopt(sys.argv[1:], "c:rf:")
    opts = dict(opts)
    part, rse, param = args[:3]
    
    if "-c" in opts:
        config = ConfigDictBackend(opts["-c"])
    elif "-r" in opts:
        config = ConfigRucioBackend()
    elif "-f" in opts:
        config = ConfigFilesBackend(opts["-f"])
    
    if part == "rse":
        print(config.rse_param(rse, param))
    elif part == "scanner":
        if param == "root_list":
            print(config.get_root_list(rse))
        else:
            print(config.scanner_param(rse, param))
    elif part == "dbdump":
        print(config.dbdump_param(rse, param))
    elif part == "root":
        root, param = args[2:]
        print(config.root_param(rse, root, param))
        
        
    
