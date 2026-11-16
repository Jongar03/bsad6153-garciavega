"""Fetch monthly appliance imports and the related UN Comtrade product catalogue."""
import argparse
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
import json
import logging
import os
from pathlib import Path
import sys
import time

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://comtradeapi.un.org"
# Six-digit finished appliances; excludes parts and commercial dishwashers.
PRODUCTS = ("841810", "841821", "841829", "845011", "845012", "845019", "842211")
IDENTITY = ("typeCode", "freqCode", "period", "reporterCode", "flowCode",
            "partnerCode", "partner2Code", "classificationCode", "cmdCode",
            "customsCode", "motCode")
CAP = 100000
LOG = logging.getLogger("fetch")


def save(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def months(end, count):
    last = datetime.strptime(end, "%Y%m")
    index = last.year * 12 + last.month - 1
    return [f"{i // 12:04d}{i % 12 + 1:02d}" for i in range(index - count + 1, index + 1)]


def retry_delay(value, attempt):
    delay = min(60, 2 ** attempt)
    if value:
        try:
            return max(delay, float(value))
        except ValueError:
            try:
                return max(delay, (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds())
            except (ValueError, TypeError, OverflowError):
                pass
    return delay


class Client:
    def __init__(self, key, directory):
        self.key = key
        self.directory = directory
        self.session = requests.Session()
        self.last_request = 0.0
        self.requests = 0
        self.retries = 0
        self.failures = []

    def get(self, path, params, label, authenticated=False):
        query = dict(params)
        if authenticated:
            query["subscription-key"] = self.key
        for attempt in range(5):
            time.sleep(max(0, 1.1 - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            self.requests += 1
            delay = retry_delay(None, attempt)
            try:
                response = self.session.get(BASE + path, params=query, timeout=(10, 60))
                status = response.status_code
                if status in (401, 403):
                    raise RuntimeError("API authentication/access rejected; check COMTRADE_API_KEY and subscription.")
                if status == 429 or 500 <= status <= 599:
                    reason = f"HTTP {status}"
                    delay = retry_delay(response.headers.get("Retry-After"), attempt)
                elif status != 200:
                    self.failures.append({"partition": label, "reason": f"HTTP {status}"})
                    LOG.error("%s: HTTP %s; skipped", label, status)
                    return None
                else:
                    try:
                        payload = response.json()
                    except ValueError:
                        reason = "invalid JSON"
                    else:
                        # Never persist request URLs, headers, or credentials.
                        save(self.directory / f"{label}.json", payload)
                        return payload
            except requests.RequestException as exc:
                # Exception text can contain the authenticated URL: log only its type.
                reason = type(exc).__name__
            LOG.warning("%s: %s (attempt %s/5)", label, reason, attempt + 1)
            if attempt < 4:
                self.retries += 1
                LOG.info("Retrying in %.1f seconds", delay)
                time.sleep(delay)
        self.failures.append({"partition": label, "reason": reason})
        LOG.error("%s: retries exhausted; skipped", label)
        return None


def valid_trade(row):
    return (isinstance(row, dict)
            and all(row.get(field) is not None for field in IDENTITY)
            and isinstance(row.get("primaryValue"), (int, float))
            and not isinstance(row.get("primaryValue"), bool))


def run(args):
    load_dotenv(ROOT / ".env")
    key = os.getenv("COMTRADE_API_KEY", "").strip()
    if not key:
        LOG.error("Missing COMTRADE_API_KEY; set it in the project .env file.")
        return 1
    directory = ROOT / "data" / "raw" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    directory.mkdir(parents=True)
    handler = logging.FileHandler(directory / "fetch.log", encoding="utf-8")
    LOG.addHandler(handler)
    client = Client(key, directory)
    summary = {"started_at": datetime.now(timezone.utc).isoformat(), "periods": months(args.end, args.months),
               "product_codes": PRODUCTS, "unique_trade_records": 0, "invalid_records": 0,
               "duplicate_records": 0, "empty_periods": [], "related_products": 0, "complete": False}
    seen = set()
    sample = []
    products = []
    try:
        reference = client.get("/files/v1/app/reference/HS.json", {}, "products")
        if not isinstance(reference, dict) or not isinstance(reference.get("results"), list):
            raise RuntimeError("Product catalogue missing or malformed.")
        products = [r for r in reference["results"] if isinstance(r, dict)
                    and r.get("id") in PRODUCTS and r.get("text")]
        if {r["id"] for r in products} != set(PRODUCTS):
            raise RuntimeError("Selected products missing from catalogue.")
        summary["related_products"] = len(products)
        for period in summary["periods"]:
            params = {"reporterCode": 842, "period": period, "cmdCode": ",".join(PRODUCTS),
                      "flowCode": "M", "partner2Code": 0, "customsCode": "C00", "motCode": 0,
                      "maxRecords": CAP, "includeDesc": "true", "breakdownMode": "classic"}
            payload = client.get("/data/v1/get/C/M/HS", params, f"trade_{period}", authenticated=True)
            if payload is None:
                continue
            rows = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(rows, list):
                client.failures.append({"partition": period, "reason": "missing data array"})
                LOG.error("%s: missing data array; skipped", period)
                continue
            if len(rows) >= CAP:
                client.failures.append({"partition": period, "reason": "record cap reached; split query further"})
                LOG.error("%s: possible truncation; not counting partition", period)
                continue
            if not rows:
                summary["empty_periods"].append(period)
            invalid = 0
            for row in rows:
                if not valid_trade(row):
                    invalid += 1
                    continue
                identity = tuple(row[field] for field in IDENTITY)
                if identity in seen:
                    summary["duplicate_records"] += 1
                    continue
                seen.add(identity)
                if len(sample) < 5:
                    sample.append(row)
            summary["invalid_records"] += invalid
            LOG.info("%s: %s rows, %s invalid skipped; %s unique total", period, len(rows), invalid, len(seen))
        summary["complete"] = len(seen) >= 500 and not client.failures and summary["invalid_records"] == 0
        if args.write_sample and sample:
            save(ROOT / "data" / "sample" / "comtrade_sample.json", {
                "source": "UN Comtrade", "retrieved_at": summary["started_at"],
                "note": "Small excerpt of raw records; not a complete API response.",
                "trade_records": sample, "products": products})
    except RuntimeError as exc:
        LOG.error("%s", exc)
        summary["error"] = str(exc)
    finally:
        summary.update(unique_trade_records=len(seen), requests=client.requests, retries=client.retries,
                       failed_partitions=client.failures, finished_at=datetime.now(timezone.utc).isoformat())
        save(directory / "summary.json", summary)
        client.session.close()
        LOG.info("Result: %s trade records; %s related products; %s retries; %s failures",
                 len(seen), len(products), client.retries, len(client.failures))
        LOG.info("Raw responses and report: %s", directory)
        LOG.removeHandler(handler)
        handler.close()
    if not summary["complete"]:
        LOG.error("Incomplete run: requires 500 valid unique records and no unresolved failures. See summary.json.")
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    # Previous completed calendar month; recent months may not yet be published.
    today = date.today()
    previous = today.year * 12 + today.month - 2
    parser.add_argument("--end", default=f"{previous // 12:04d}{previous % 12 + 1:02d}", help="Last month, YYYYMM")
    parser.add_argument("--months", type=int, default=24, help="Monthly partitions (1-120)")
    parser.add_argument("--write-sample", action="store_true", help="Replace the small public sample")
    args = parser.parse_args()
    try:
        if len(args.end) != 6 or not 1 <= args.months <= 120:
            raise ValueError
        months(args.end, args.months)
    except ValueError:
        parser.error("Use --end YYYYMM and --months between 1 and 120.")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        return run(args)
    except OSError:
        LOG.error("Unable to read/write project files; check permissions and free disk space.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
