import argparse
import hashlib
import json
import re
import ssl
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPSHandler, HTTPRedirectHandler

import certifi

USER_AGENT = "AuthorizedHTMLCollector/1.0"



class SafeRedirect(HTTPRedirectHandler):
    def __init__(self, allowed_hosts):
        super().__init__()
        self.allowed_hosts = allowed_hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlparse(newurl)
        if parsed.scheme != "https" or (parsed.hostname or "").lower() not in self.allowed_hosts:
            raise ValueError("Redirect blocked: destination is not HTTPS/allowlisted")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def safe_url(url, allowed_hosts):
    parsed = urlparse(url.strip())
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError(f"Only HTTPS URLs are accepted: {url}")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are rejected")
    if parsed.hostname.lower() not in allowed_hosts:
        raise ValueError(f"Host is not allowlisted: {parsed.hostname}")
    return url.strip()


def slug_for(url):
    digest = hashlib.sha256(url.encode()).hexdigest()[:16]
    path = urlparse(url).path.rstrip("/").split("/")[-1]
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", path)[:40] or "page"
    return f"{slug}_{digest}.html"


def fetch(url, allowed_hosts, max_bytes, timeout):
    context = ssl.create_default_context(cafile=certifi.where())
    opener = build_opener(HTTPSHandler(context=context), SafeRedirect(allowed_hosts))
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    with opener.open(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "").lower()
        if "html" not in content_type:
            raise ValueError(f"Rejected content type: {content_type or 'missing'}")
        data = response.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError(f"Response exceeds size limit ({max_bytes} bytes)")
        return data, response.geturl(), response.status, content_type



def load_state(path):
    if not path.exists():
        return {"completed": {}, "errors": {}}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(state, dict) or not isinstance(state.get("completed", {}), dict) or not isinstance(state.get("errors", {}), dict):
            raise ValueError("Unexpected state structure")
        return state
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        raise SystemExit(f"State file is invalid; back it up and use --reset if appropriate: {exc}")


def write_json_atomic(path, obj):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)


def main():
    parser = argparse.ArgumentParser(description="Collect explicitly listed HTML pages from allowlisted HTTPS hosts.")
    parser.add_argument("--urls", default="urls.txt", help="Text file with one HTTPS URL per line")
    parser.add_argument("--output", default="collected", help="Output directory")
    parser.add_argument("--allow-host", action="append", required=True, help="Allowed hostname; repeat as needed")
    parser.add_argument("--max-bytes", type=int, default=2 * 1024 * 1024)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests, seconds")
    parser.add_argument("--reset", action="store_true", help="Reset saved state (does not delete existing HTML files)")
    args = parser.parse_args()
    if args.max_bytes <= 0 or args.timeout <= 0 or args.delay < 0:
        parser.error("--max-bytes and --timeout must be positive; --delay cannot be negative")

    allowed = {h.lower().strip() for h in args.allow_host if h.strip()}
    urls_file = Path(args.urls)
    if not urls_file.exists():
        parser.error(f"URL list not found: {urls_file}")
    urls = [line.strip() for line in urls_file.read_text(encoding="utf-8").splitlines() if line.strip() and not line.lstrip().startswith("#")]
    urls = [safe_url(u, allowed) for u in urls]
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    state_path = out / "state.json"
    state = {"completed": {}, "errors": {}} if args.reset else load_state(state_path)
    index = []
    for url in urls:
        if url in state["completed"]:
            print(f"SKIP already saved: {url}")
            continue
        try:
            body, final_url, status, ctype = fetch(url, allowed, args.max_bytes, args.timeout)
            filename = slug_for(url)
            target = out / filename
            temp = target.with_suffix(target.suffix + ".tmp")
            temp.write_bytes(body)
            temp.replace(target)
            state["completed"][url] = {"file": filename, "bytes": len(body), "status": status, "final_url": final_url}
            state["errors"].pop(url, None)
            print(f"SAVED {filename} ({len(body)} bytes)")
        except Exception as exc:
            state["errors"][url] = str(exc)
            print(f"ERROR {url}: {exc}")
        write_json_atomic(state_path, state)
        time.sleep(args.delay)
    index = [{"url": u, **state["completed"][u]} for u in urls if u in state["completed"]]
    write_json_atomic(out / "index.json", {"pages": index, "errors": state["errors"]})
    print(f"Finished: {len(index)} saved, {len(state['errors'])} error(s)")

if __name__ == "__main__":
    main()
