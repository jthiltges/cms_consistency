Moving Consistency Enforcement into Rucio configuration
=======================================================

Consistency Enformenet Procedures (CEP) will get their configuration from 2 sources in live Rucio instance:

-  Rucio Configuration - part of Rucio database, which mimics popular .ini configuratiin file format.
   This portion will be used to store common, RSE-independent configuration and RSE configuration defaults.

- RSE attributes will be used to store RSE-specific parameters such as xrootd server address and server root
  path, list of roots to scan.

Confuguration Conversion Procedure
----------------------------------

1. Have Rucio client configured and log in as Rucio root account

2. Pull the code repository

   .. code-block:: bash
   
       $ git pull https://github.com/ivmfnal/cms_consistency.git cms-consistency-new
       $ cd cms-consistency-new
       $ git checkout config_in_rucio
       $ cd rucio-config

   
3. Import defaults:

   .. code-block:: bash
        
        $ python import_cfg.py cc_defaults.cfg
        
4. View the results

   .. code-block:: bash
        
        $ python export_cfg.py -s consistency_enforcement
        
5. Import RSE-specific configuration

   .. code-block:: bash
        
        $ python import_rse_cfg.py <current_config.yaml>
        
6. View the results

   .. code-block:: bash
        
        $ rucio-admin rse info <rse>

            

        
		
		