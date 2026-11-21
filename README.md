# HTML Collector (authorized, allowlisted)

A small HTML collector for pages you own or are authorized to retrieve. It accepts an explicit URL list; it does not enumerate IDs or crawl arbitrary sites.

## Requirements
- Python 3.11+
- `pip install -r requirements.txt`

## Usage
1. Create `urls.txt`, one HTTPS URL per line, from an authorized source.
2. Set allowed hostnames (comma-separated) explicitly:
   `python -m collector --urls urls.txt --output collected --allow-host example.com`
3. Resume state is stored under `collected/state.json`. Use `--reset` to reset it.
4. Output pages are saved as individual HTML files. `index.json` summarizes results.

SSL verification is enabled. If CA certificates are unavailable, install/update system `ca-certificates` or update `certifi`; never disable verification.

Responses are size-limited (default 2 MiB). Redirects are restricted to allowlisted hosts.

Treat saved HTML as untrusted content; do not open it with scripts enabled.
