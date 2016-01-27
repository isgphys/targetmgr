Wrapper for rtslib by ISG D-PHYS ETHZ to manage iSCSI targets.

Reads the configuration from `./targetmgr.json` and
creates the corresonding iSCSI targets.

Further documentation:

    - rtslib:  http://linux-iscsi.org/Doc/rtslib/html/
    - logging: https://docs.python.org/2/howto/logging.html

CLI options:

    --delete    deletes all existing iSCSI resources
    -h          show this help
    -d          show DEBUG output
