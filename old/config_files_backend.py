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


