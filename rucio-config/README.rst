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

   
3. Import existing configuration into Rucio:

    .. code-block:: bash
        
        $ python import_cc_config.py config.yaml

    This will create ``consistency_enforcement`` and 2 subsections: ``consistency_enforcement.scanner`` and 
    ``consistency_enforcement.dbdump``. If these sections existed before, all their contents will be removed and replaced
    with new values.
    
        
4. View the results

   .. code-block:: bash
        
        $ rucio-admin config get
        $ rucio-admin rse info <RSE name>
        
Running CC tools with new configuration
---------------------------------------

    .. code-block:: bash
    
        $ python xrootd_scanner.py -c config.yaml ...          # use the config file
        $ python xrootd_scanner.py ...                         # use the configuration stored in Rucio
        
        $ python db_dump.py -c config.yaml ...                 # use the config file
        $ python db_dump.py ...                                # use the configuration stored in Rucio
        
Rucio configuration structure
-----------------------------

RSE defaults
============

RSE defaults are stored in the Rucio database, which mimics the .ini file structure, implemented by the standard Python library class
ConfigParser. The configiration is organized into named sections and each section is a set of named attributes with their values.
Rucio supports only scalar sctings as configuration parameter values. Integer values are represented as decimals and interpreted
by the CC tools.

RSE defaults are organized into 3 sections:

Section consistency_enforcement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section has only one parameter ``npartitions`` - the number of partitions to split file lists into. This parameter is used
by both DB dump tool and the xrootd scanner.
    
Section consistency_enforcement.scanner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section has parameters used only by the xrootd scanner:

recursion - integer
    Directory depth level, relative to the root, at which to start attempting recursive scanning
    
nworkers - integer
    The number of parallel scanners to run
    
timeout - integer
    Time-out for scanning an individual directory. If the directory is scanned recursively and the scanning times-out, the
    scanner will attempt to scan it non-recursively and then scan recursively all its subdirectories
    
server_root, string
    Path to the very top of the server namespace. Scan roots are specified relative to the ``server_root``
    
remove_prefix, add_prexix - strings
    These two parameters specify the path-to-LFN conversion procedure applied to each file path found by the scanner:
    
        1. Remove the ``remove_prefix`` from physical path
        2. Add the ``add_prefix``
        
    Defaults are "/"
    
roots - string
    JSON representation of the list of root configuration dictionaries. Each dictionary contains the following elements:
    
        * path - required, path of the ``root``, relative to the ``server_root``
        * ignore - optional, list of subdirectory paths, relative to the ``root``, to remove from the scanner output
        
Section consistency_enforcement.dbdump
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section has parameters used by the DB dump tool:

path_root - string
    The top of the LFN namespace tree to dump. Default is "/"
    
ignore - string
    Space-separated list of paths to ignore, relative to the ``path_root``


    



