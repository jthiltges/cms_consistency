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
        

