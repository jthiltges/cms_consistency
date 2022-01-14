import re, os, json
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
        # returns None if no roots defined for the RSE
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
        roots = self.scanner_param(rse_name, "roots")
        root_rse = self.get_root(root, rse_name) or {}
        root_common = self.get_root(root)
        print(f"Backend.root_param({rse_name},{root},{param}):")
        print("  root_rse:", root_rse)
        print("  root_common:", root_common)
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

    def root_list(self, rse):
        lst = self.get_root_list(rse)
        if lst is None:
            lst = self.get_root_list("*") or []
        return lst
        
class ConfigYAMLBackend(ConfigBackend):
    
    def __init__(self, cfg):
        # cfg is either YAML file path or a dictionary read from the YAML file
        if isinstance(cfg, str):
            import yaml
            cfg = yaml.load(open(cfg, "r"), Loader=yaml.SafeLoader)
        cfg = cfg.get("rses", {})
        self.Config = cfg
        self.Roots = {}             # {rse -> {root -> root_config}} 
        for rse, data in cfg.items():
            roots = data.get("scanner", {}).get("roots")
            if roots is not None:
                self.Roots[rse] = self.roots_as_dict(roots)
        #print("ConfigYAMLBackend.Config:", self.Config)
        print("ConfigYAMLBackend.__init__: Roots:", self.Roots)

    def get_config(self, rse="*"):
        cfg = self.Config.get(rse, {})
        #print(f"get_config({rse}): cfg:", cfg)
        return self.Config.get(rse, {})
        
    def get_root_list(self, rse="*"):
        roots = self.Roots.get(rse)
        if roots is not None:
            roots = list(roots.keys())
        return roots
        
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
        lst = self.Roots.get(rse)
        if lst is not None:
            lst = list(lst.keys())
        return lst
        
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
        self.CommonRoots = {}

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
                roots = cfg.get("scanner", {}).get("roots")
                print(f"Rucio backend get_config({rse}): roots:", roots)
                if roots is not None:
                    roots = self.roots_as_dict(roots)
                self.RSERoots[rse] = roots
            return cfg
        
    def get_root_list(self, rse="*"):
        if rse == "*":
            lst = self.get_config("*").get("scanner", {}).get("roots")
            if lst is not None:
                lst = lst.split()
        else:
            cfg = self.get_config(rse)  # this will fetch self.RSERoots[rse] as dict
            lst = self.RSERoots.get(rse)
            if lst is not None:
                lst = list(lst.keys())
        print(f"get_root_list({rse}): lst:", lst)
        return lst
            
    def get_root(self, root, rse="*"):
        if rse == "*":
            if not root in self.CommonRoots:
                root_cfg = None
                try:    root_cfg = self.ConfigClient.get_config(self.CONFIG_SECTION_PREFIX + ".scanner.root." + root)
                except: pass
                self.CommonRoots[root] = root_cfg
            return self.CommonRoots.get(root) or {}
        else:
            if rse not in self.RSERoots:
                self.get_config(rse)       # this will load self.RSERoots[rse_name], if any
            cfg = (self.RSERoots.get(rse) or {}).get(root)
            print(f"Rucio backend: get_root({root}, {rse}): cfg:", cfg)
            return cfg
        
class CCConfiguration(object):
    
    def __init__(self, backend, rse):
        self.Backend = backend
        self.RSE = rse

        self.NPartitions = int(backend.rse_param(rse, "npartitions"))

        self.Server = backend.scanner_param(rse, "server", required=True)
        self.ServerRoot = backend.scanner_param(rse, "server_root", "/store", required=True)
        self.ScannerTimeout = int(backend.scanner_param(rse, "timeout", 300))
        self.RootList = backend.root_list(rse)
        self.RemovePrefix = backend.scanner_param(rse, "remove_prefix", "/")
        self.AddPrefix = backend.scanner_param(rse, "add_prefix", "/store/")
        self.NWorkers = int(backend.scanner_param(rse, "nworkers", 8))
        self.IncludeSizes = backend.scanner_param(rse, "include_sizes", "yes") == "yes"
        self.RecursionThreshold = int(backend.scanner_param(rse, "recursion", 1))

        self.DBDumpPathRoot = backend.dbdump_param(rse, "path_root", "/")
        self.DBDumpIgnoreSubdirs = backend.dbdump_param(rse, "ignore", [])

    def scanner_ignore_subdirs(self, root):
        return self.Backend.root_param(self.RSE, root, "ignore", [])

    @staticmethod
    def rse_config(rse, backend_type, *backend_args):
        if backend_type == "rucio":
            backend = ConfigRucioBackend(*backend_args)
        elif backend_type == "yaml":
            backend = ConfigYAMLBackend(*backend_args)
        else:
            raise ValueError(f"Unknown configuration backend type {backend_type}")
        return CCConfiguration(backend, rse)

if __name__ == "__main__":
    import sys, getopt
    opts, args = getopt.getopt(sys.argv[1:], "c:rf:")
    opts = dict(opts)
    part, rse, param = args[:3]
    
    if "-c" in opts:
        config = ConfigYAMLBackend(opts["-c"])
    elif "-r" in opts:
        config = ConfigRucioBackend()
    elif "-f" in opts:
        config = ConfigFilesBackend(opts["-f"])
    
    if part == "rse":
        print(config.rse_param(rse, param))
    elif part == "scanner":
        if param == "root_list":
            print(config.root_list(rse))
        else:
            print(config.scanner_param(rse, param))
    elif part == "dbdump":
        print(config.dbdump_param(rse, param))
    elif part == "root":
        root, param = args[2:]
        print(config.root_param(rse, root, param))
        
        
    

