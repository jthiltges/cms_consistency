Moving Consistency Enforcement into Rucio configuration
=======================================================

Consistency Enformenet Procedures (CEP) will get their configuration from 2 sources in live Rucio instance:

-  Rucio Configuration - part of Rucio database, which mimics popular .ini configuratiin file format.
   This portion will be used to store common, RSE-independent configuration and RSE configuration defaults:

.. code-block:: 

	[consistency_enforcement]
	npartitions = 5
	ignore = /store/backfill
		/store/test
		/store/unmerged
		/store/temp

	[consistency_enforcement.scanner]
	server_root = /store/
	timeout = 300
	remove_prefix = /
	add_prefix = /store/
	nworkers = 8
	recursion = 1
	include_sizes = yes
	roots = express
	      mc
	      data
	      generator
	      results
	      hidata
	      himc
	      relval
    
	[consistency_enforcement.db_dump]
    path_root = /
    
- RSE attributes will be used to store RSE-specific parameters such as xrootd server address and server root
  path, list of roots to scan.

Confuguration Conversion Procedure
----------------------------------

    1. Have Rucio client configured and log in as Rucio root account
    
    2. After getting cms_consistency repositiory from github (https://github.com/ivmfnal/cms_consistency.git),
       go to rucio-config subdirectory.
       
    3. Import defaults:
    
        .. code-block:: bash
            
            $ python import_cfg.py cc_defaults.cfg
            
    4. View the results
    
        .. code-block:: bash
            
            $ python export_cfg.py -s consistency_enforcement
            
    5. Import RSE-specific configuration
    
        .. code-block:: bash
            
            $ python import_rse_cfg.py <current_config.yaml>
            

        
		
		