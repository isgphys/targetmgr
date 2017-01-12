targetmgr
=========

Wrapper for rtslib developed and used by [IT Services Group](http://isg.phys.ethz.ch) of the Physics Department at ETH Zurich to manage our iSCSI targets.

Testet and works with >= **Ubuntu Xenial 16.04**

Further documentation:

    - rtslib:  http://linux-iscsi.org/Doc/rtslib/html/

Reads the configuration from `./targetmgr.json` and
creates the corresonding iSCSI targets.

#### targetmgr.json

```
{
    "targets": [
        {
            "iqn":           "iqn.2016-01.ch.ethz.phys.storage1-dev:firstBundle",
            "iqn_initiator": "iqn.2016-01.ch.ethz.phys.storage-gw-dev",
            "portal":        "192.168.20.110",
            "luns": [
                {
                    "name":   "test_1",
                    "device": "/dev/vgstorage01b/1g-chunk-01"
                },
                {
                    "name":   "test_2",
                    "device": "/dev/vgstorage01b/1g-chunk-02"
                },
                {
                    "name":   "test_3",
                    "device": "/dev/vgstorage01b/1g-chunk-03"
                }
            ]
        },
        {
            "iqn":           "iqn.2016-01.ch.ethz.phys.storage1-dev:secondBundle",
            "iqn_initiator": "iqn.2016-01.ch.ethz.phys.storage-gw-dev",
            "portal":        "192.168.20.110",
            "luns": [
                {
                    "name":   "test_4",
                    "device": "/dev/vgstorage01c/1g-chunk-01"
                },
                {
                    "name":   "test_5",
                    "device": "/dev/vgstorage01c/1g-chunk-02"
                }
            ]
        }
    ]
}
```

#### targetcli output

```
o- / ............................................................................................. [...]
  o- backstores .................................................................................. [...]
  | o- iblock ...................................................................... [5 Storage Objects]
  | | o- test_1 .............................................. [/dev/vgstorage01b/1g-chunk-01 activated]
  | | o- test_2 .............................................. [/dev/vgstorage01b/1g-chunk-02 activated]
  | | o- test_3 .............................................. [/dev/vgstorage01b/1g-chunk-03 activated]
  | | o- test_4 .............................................. [/dev/vgstorage01c/1g-chunk-01 activated]
  | | o- test_5 .............................................. [/dev/vgstorage01c/1g-chunk-02 activated]
  o- iscsi ................................................................................. [2 Targets]
    o- iqn.2016-01.ch.ethz.phys.storage1-dev:firstBundle ....................................... [1 TPG]
    | o- tpgt1 .............................................................................. [disabled]
    |   o- acls ................................................................................ [1 ACL]
    |   | o- iqn.2016-01.ch.ethz.phys.storage-gw-dev ................................... [3 Mapped LUNs]
    |   |   o- mapped_lun0 ................................................................. [lun0 (rw)]
    |   |   o- mapped_lun1 ................................................................. [lun1 (rw)]
    |   |   o- mapped_lun2 ................................................................. [lun2 (rw)]
    |   o- luns ............................................................................... [3 LUNs]
    |   | o- lun0 ...................................... [iblock/test_1 (/dev/vgstorage01b/1g-chunk-01)]
    |   | o- lun1 ...................................... [iblock/test_2 (/dev/vgstorage01b/1g-chunk-02)]
    |   | o- lun2 ...................................... [iblock/test_3 (/dev/vgstorage01b/1g-chunk-03)]
    |   o- portals .......................................................................... [1 Portal]
    |     o- 192.168.20.110:3260 ................................................... [OK, iser disabled]
    o- iqn.2016-01.ch.ethz.phys.storage1-dev:secondBundle ...................................... [1 TPG]
      o- tpgt1 .............................................................................. [disabled]
        o- acls ................................................................................ [1 ACL]
        | o- iqn.2016-01.ch.ethz.phys.storage-gw-dev ................................... [2 Mapped LUNs]
        |   o- mapped_lun0 ................................................................. [lun0 (rw)]
        |   o- mapped_lun1 ................................................................. [lun1 (rw)]
        o- luns ............................................................................... [2 LUNs]
        | o- lun0 ...................................... [iblock/test_4 (/dev/vgstorage01c/1g-chunk-01)]
        | o- lun1 ...................................... [iblock/test_5 (/dev/vgstorage01c/1g-chunk-02)]
        o- portals .......................................................................... [1 Portal]
          o- 192.168.20.110:3260 ................................................... [OK, iser disabled]
```

#### CLI options

    --delete    deletes all existing iSCSI resources
    -h          show this help
    -d          show DEBUG output


Author
------

Patrick Schmid (schmid@phys.ethz.ch)


License
-------

> targetmgr - Wrapper for rtslib to manage iSCSI targets
>
> Copyright 2016 Patrick Schmid
>
> This program is free software: you can redistribute it and/or modify
> it under the terms of the GNU General Public License as published by
> the Free Software Foundation, either version 3 of the License, or
> (at your option) any later version.
>
> This program is distributed in the hope that it will be useful,
> but WITHOUT ANY WARRANTY; without even the implied warranty of
> MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
> GNU General Public License for more details.
