# CryptoBib Database Import

**WARNING**: This is probably not the repository your are interested in. This repository is only for *cryptobib* developers. The repositories containing the public *bib* files are [cryptobib/export](https://github.com/cryptobib/export) and  [cryptobib/export_crossref](https://github.com/cryptobib/export_crossref).

**WARNING**: This project shall only be used as a subfolder of the main project [cryptobib/cryptobib](https://github.com/cryptobib/cryptobib). Please read the documentation of the main project.

## Setup

`import.py` looks up DBLP publications in a local copy of the [DBLP XML dump](https://dblp.org/faq/How+can+I+download+the+whole+dblp+dataset.html) instead of fetching each one over the network. Fetch/refresh it with:

```bash
python3 fetch_dblp_dump.py
```

This downloads `dblp.xml.gz` + `dblp.dtd` into `db_import/dblp-dump/` (skipping the download if the local copy's checksum already matches). Re-run it occasionally to pick up new publications; entries not yet in the dump fall back to a live DBLP fetch automatically.
