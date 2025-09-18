# FDIC Failed Banks – Static Site Generator

This project generates a static website visualizing **failed banks in the United States** using data from the FDIC.  
It builds an interactive map, state pages, and bank pages, all rendered from a SQLite database.


## Requirements

- Python 3.11+
- Dependencies (install via uv):

## Commands

### Generate sqlite database
``` bash
uv run python scripts/generate_site.py
```
### Generate Website
__requires db file `fdic_failed_banks.db` in root of directory(see generating sqlite database)__
``` bash
uv run python scripts/create_db.py
```

### Runing Dev server
``` bash
uv run python scripts/dev_server.py
```
