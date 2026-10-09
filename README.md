# teslaskin — custom wraps for Tesla Model Y

Generates Paint Shop wraps (PNG 1024x1024, <1 MB) masked to the official
Model Y template (`templates/modely_template.png`, from
[teslamotors/custom-wraps](https://github.com/teslamotors/custom-wraps)).

## Install on car

**USB**
1. Format drive exFAT / FAT32 / ext4 (not NTFS), no map/firmware files on it.
2. Create folder `Wraps` at drive root, copy the PNGs from `wraps/` into it (max 10).
3. Plug in car, then Toybox → Paint Shop → Wraps tab.

**Mobile app** (v4.59.0+): Creations → Wrap → Upload.

## Make more

Edit/add a function in `make_wraps.py`, register it in `SKINS`, run
`python3 make_wraps.py` (needs Pillow + numpy). File names: letters, digits,
`_`, `-`, space only, max 30 chars.

Other Tesla model/year? Download its template from the repo above and run
`python3 make_wraps.py path/to/template.png`.
