#!/usr/bin/env python3
import argparse, sys, json, re
from pathlib import Path

BUILD_TYPES = {"build-system", "build", "ci", "continuous-integration", "distribution", "vcs"}
PROP_URL_REGEX = re.compile(r"(build|ci|pipeline|artifact).*url", re.IGNORECASE)

def load_sbom(path):
    data = Path(path).read_text()
    # Heuristic: JSON if it starts with { or [
    if data.lstrip().startswith(("{", "[")):
        return "json", json.loads(data)
    # Otherwise try CycloneDX XML
    try:
        import xmltodict  # pip install xmltodict
    except Exception as e:
        print("For XML SBOMs, install xmltodict: pip install xmltodict", file=sys.stderr)
        raise
    xml = xmltodict.parse(data)
    return "xml", xml

def iter_components(kind, doc):
    if kind == "json":
        for c in (doc.get("components") or []):
            yield c
    else:
        # XML structure: bom.components.component (can be dict or list)
        bom = doc.get("bom", {})
        comps = (((bom.get("components") or {}).get("component")) or [])
        if isinstance(comps, dict):
            comps = [comps]
        for c in comps:
            yield c

def get_field(d, key, default=""):
    if isinstance(d, dict):
        return d.get(key, default)
    return default

def normalize_props(obj, kind):
    if kind == "json":
        return obj.get("properties") or []
    # XML: properties.property => list of {"name": "...", "value": "..."}
    props = get_field(obj, "properties", {})
    prop = get_field(props, "property", [])
    if isinstance(prop, dict):
        prop = [prop]
    # Normalize keys
    out = []
    for p in prop:
        out.append({"name": get_field(p, "@name") or get_field(p, "name", ""),
                    "value": get_field(p, "#text") or get_field(p, "value", "")})
    return out

def normalize_extrefs(obj, kind):
    if kind == "json":
        return obj.get("externalReferences") or []
    # XML: externalReferences.reference with @type and url child
    ex = get_field(obj, "externalReferences", {})
    ref = get_field(ex, "reference", [])
    if isinstance(ref, dict):
        ref = [ref]
    out = []
    for r in ref:
        out.append({
            "type": get_field(r, "@type") or get_field(r, "type", ""),
            "url":  get_field(r, "url", "")
        })
    return out

def extract_component_row(c, kind):
    name = get_field(c, "name", "")
    version = get_field(c, "version", "")
    purl = get_field(c, "purl", "")
    bom_ref = get_field(c, "bom-ref", "") if kind == "json" else get_field(c, "@bom-ref", "")

    build_urls = []

    # externalReferences
    for r in normalize_extrefs(c, kind):
        rtype = (r.get("type") or "").strip().lower()
        url = (r.get("url") or "").strip()
        if url and (rtype in BUILD_TYPES):
            build_urls.append(url)

    # properties with *url names
    for p in normalize_props(c, kind):
        n = (p.get("name") or "")
        v = (p.get("value") or "").strip()
        if v and PROP_URL_REGEX.search(n or ""):
            build_urls.append(v)

    # dedupe, stable order
    seen = set()
    deduped = []
    for u in build_urls:
        if u not in seen:
            seen.add(u)
            deduped.append(u)

    return {
        "name": name, "version": version, "purl": purl, "bom_ref": bom_ref,
        "build_urls": deduped
    }

def main():
    ap = argparse.ArgumentParser(description="Extract components and build URLs from CycloneDX SBOM (JSON or XML).")
    ap.add_argument("sbom", help="Path to SBOM file (CycloneDX JSON or XML)")
    ap.add_argument("--format", choices=["json","csv"], default="json", help="Output format")
    args = ap.parse_args()

    kind, doc = load_sbom(args.sbom)
    rows = [extract_component_row(c, kind) for c in iter_components(kind, doc)]

    if args.format == "json":
        json.dump(rows, sys.stdout, indent=2)
    else:
        import csv
        w = csv.writer(sys.stdout)
        w.writerow(["name","version","purl","bom_ref","build_url"])
        for r in rows:
            if r["build_urls"]:
                for u in r["build_urls"]:
                    w.writerow([r["name"], r["version"], r["purl"], r["bom_ref"], u])
            else:
                w.writerow([r["name"], r["version"], r["purl"], r["bom_ref"], ""])

if __name__ == "__main__":
    main()
