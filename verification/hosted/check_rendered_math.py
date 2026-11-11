#!/usr/bin/env python3
r"""Check captured mathematical text against pinned GitHub Markdown source.

Usage (Python 3.10+, standard library only):
  check_rendered_math.py inventory --root REPO --repository owner/name \
    --revision FULL_COMMIT --page README.md --page science/results.md \
    --output math-source.json
  check_rendered_math.py check --inventory math-source.json \
    --capture math-capture.json [--contract math-contract.json] [--output result.json]

Inventory reads Git objects at the requested commit, not the working tree.
It recognizes math fences, $`...`$, $$...$$ and single-dollar inline math,
excluding ordinary code fences/spans. This is a bounded Markdown scanner,
not the hosting renderer's parser. Inspect its inventory before capture.

Capture schema (collect actual full accessible math text in document order):
  {"schema_version": 1, "repository": "owner/name", "revision": "40 hex",
   "renderer_profile": "github", "captured_at": "ISO-8601 with timezone",
   "capture_method": "how the actual hosted DOM was inspected",
   "pages": [{"path": "README.md", "url": "exact pinned inventory URL",
     "revision": "40 hex", "source_sha256": "inventory source hash",
     "errors": [], "math": [{"rendered": true, "errors": [],
       "text_source": "mathml", "text": "full text, not a sample"}]}]}
Allowed text_source values: mathml, mathjax-assistive, katex-accessibility,
renderer-accessibility. Extract one accessible representation per host;
exclude TeX annotation nodes and duplicate visual/accessibility copies.
Native MathML is valid. Empty math lists are valid for math-free pages.

Optional contract strengthens content checks without pretending to translate
arbitrary TeX. Each entry selects a path/index (1-based) and source_sha256
(the expression hash in inventory), with expected_text and/or required_text:
  {"schema_version": 1, "expressions": [{"path": "README.md", "index": 1,
    "source_sha256": "expression hash", "required_text": ["d", "(C1)"],
    "expected_text": "|A|<d.(C1)"}]}
Whitespace, Unicode math styling and invisible formatting are normalized.
For a demonstrated renderer-specific exception, an entry may additionally
set relation_override (symbol: count) or allow_html_like_inequality=true.
Either exception REQUIRES expected_text, a nonempty reason and an evidence
pointer. It cannot bypass missing hosts, labels, errors or source identity.
This is not a universal macro ban. Unknown TeX macros are not expanded.

The result checks expression counts, visible relations/labels and any supplied
text contract. It does NOT authenticate capture provenance, fetch a browser,
prove arbitrary TeX equivalence or scientific correctness, or inspect pixels.
Actual capture identity must be established by its collection workflow.
Visual review of equation bodies/layout remains necessary even after PASS.
Zero renderer errors alone never constitutes completeness evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import unicodedata
from urllib.parse import quote


RELATIONS = {
    "lt": "<", "gt": ">", "le": "≤", "leq": "≤", "ge": "≥", "geq": "≥",
    "ne": "≠", "neq": "≠", "in": "∈", "notin": "∉", "subset": "⊂",
    "subseteq": "⊆", "supset": "⊃", "supseteq": "⊇", "approx": "≈",
    "simeq": "≃", "equiv": "≡", "propto": "∝", "cong": "≅", "sim": "∼",
    "to": "→", "rightarrow": "→", "Rightarrow": "⇒", "implies": "⇒",
    "mapsto": "↦", "leftrightarrow": "↔", "Leftrightarrow": "⇔", "iff": "⇔",
}
RELATION_SYMBOLS = set("<>=") | set(RELATIONS.values())
COMMAND = re.compile(r"\\([A-Za-z]+)")
LABEL = re.compile(r"\\tag(\*)?\{([^{}]+)\}|\\text\{\s*\(([^{}()]+)\)\s*\}")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})([^\n]*)\n?$")
SHA = re.compile(r"[0-9a-f]{40}")
TEXT_SOURCES = {"mathml", "mathjax-assistive", "katex-accessibility", "renderer-accessibility"}


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compact(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKC", text)
                   if not c.isspace() and unicodedata.category(c) != "Cf")


def escaped(text: str, index: int) -> bool:
    backslashes = 0
    while index > 0 and text[index - 1] == "\\":
        backslashes += 1
        index -= 1
    return bool(backslashes % 2)


def tex_body(text: str) -> str:
    """Drop unescaped TeX comments; do not expand user macros."""
    return "\n".join(line[:next((i for i, c in enumerate(line)
                               if c == "%" and not escaped(line, i)), len(line))]
                     for line in text.splitlines())


def relations(tex: str) -> dict[str, int]:
    expanded = COMMAND.sub(lambda m: RELATIONS.get(m.group(1), m.group(0)), tex_body(tex))
    return dict(sorted(Counter(c for c in expanded if c in RELATION_SYMBOLS).items()))


def labels(tex: str) -> list[str]:
    return [compact(tag if star else f"({tag or text})")
            for star, tag, text in LABEL.findall(tex_body(tex))]


def expressions(source: str) -> list[dict]:
    """Return ordered source spans; reject unterminated recognized delimiters."""
    found: list[dict] = []

    def add(tex: str, offset: int, end: int, kind: str) -> None:
        found.append({"line_start": source.count("\n", 0, offset) + 1,
                      "line_end": source.count("\n", 0, end) + 1,
                      "kind": kind, "tex": tex, "source_sha256": digest(tex),
                      "relations": relations(tex), "labels": labels(tex)})

    def prose(start: int, end: int) -> None:
        i = start
        while i < end:
            if source[i] == "$" and not escaped(source, i):
                opener, closer, kind = ("$`", "`$", "github-inline") if source.startswith("$`", i) else (
                    ("$$", "$$", "dollar-display") if source.startswith("$$", i)
                    else ("$", "$", "dollar-inline"))
                j = source.find(closer, i + len(opener), end)
                while j >= 0 and escaped(source, j):
                    j = source.find(closer, j + len(closer), end)
                if j < 0 or (kind == "dollar-inline" and "\n" in source[i:j]):
                    raise ValueError(f"unclosed {kind} at line {source.count(chr(10), 0, i) + 1}")
                add(source[i + len(opener):j], i, j + len(closer) - 1, kind)
                i = j + len(closer)
            elif source[i] == "`" and not escaped(source, i):
                n = 1
                while i + n < end and source[i + n] == "`":
                    n += 1
                j = source.find("`" * n, i + n, end)
                i = j + n if j >= 0 else i + n
            else:
                i += 1

    lines = source.splitlines(keepends=True)
    offset = start = i = 0
    while i < len(lines):
        match = FENCE.match(lines[i])
        if not match:
            offset += len(lines[i])
            i += 1
            continue
        prose(start, offset)
        marker, info = match.groups()
        begin = offset
        offset += len(lines[i])
        body_start = offset
        i += 1
        while i < len(lines):
            closing = FENCE.match(lines[i])
            if closing and closing[1][0] == marker[0] and len(closing[1]) >= len(marker) and not closing[2].strip():
                break
            offset += len(lines[i])
            i += 1
        if i == len(lines):
            raise ValueError(f"unclosed code fence at line {source.count(chr(10), 0, begin) + 1}")
        if info.strip() == "math":
            add(source[body_start:offset], begin, offset, "math-fence")
        offset += len(lines[i])
        i += 1
        start = offset
    prose(start, len(source))
    for index, item in enumerate(found, 1):
        item["index"] = index
    return found


def safe_path(path: str) -> bool:
    return isinstance(path, str) and bool(path) and "\\" not in path and not PurePosixPath(path).is_absolute() and all(
        part not in {"", ".", ".."} for part in path.split("/"))


def make_inventory(repository: str, revision: str, sources: dict[str, str]) -> dict:
    if not isinstance(repository, str) or not isinstance(revision, str) or not re.fullmatch(
            r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) or not SHA.fullmatch(revision):
        raise ValueError("use owner/name and an exact lowercase 40-character commit SHA")
    if not isinstance(sources, dict) or not sources or not all(
            safe_path(p) and isinstance(s, str) for p, s in sources.items()):
        raise ValueError("supply at least one safe repository-relative page path")
    return {"schema_version": 1, "repository": repository, "revision": revision,
            "renderer_profile": "github", "pages": [
                {"path": path, "url": f"https://github.com/{repository}/blob/{revision}/{quote(path, safe='/')}",
                 "source_sha256": digest(source), "source_text": source, "expressions": expressions(source)}
                for path, source in sources.items()]}


def validate(inventory: dict, capture: dict, contract: dict | None = None) -> dict:
    """Return failures rather than equating a passing text check with readiness."""
    failures: list[str] = []
    boundaries: list[dict] = []
    exceptions: list[dict] = []
    if not isinstance(inventory, dict) or not isinstance(capture, dict):
        raise ValueError("inventory and capture must be JSON objects")
    if type(inventory.get("schema_version")) is not int or type(capture.get("schema_version")) is not int or inventory["schema_version"] != 1 or capture["schema_version"] != 1:
        raise ValueError("unsupported inventory or capture schema_version")
    pages = inventory.get("pages")
    if not isinstance(pages, list) or not pages or any(not isinstance(p, dict) for p in pages):
        raise ValueError("inventory needs a nonempty pages array")
    paths = [p.get("path") for p in pages]
    if any(not isinstance(p, str) for p in paths) or len(set(paths)) != len(paths):
        raise ValueError("inventory page paths must be unique strings")
    rebuilt = make_inventory(inventory.get("repository", ""), inventory.get("revision", ""),
                             {p["path"]: p["source_text"] for p in pages})
    if inventory != rebuilt:
        raise ValueError("inventory does not match its embedded source bytes/expression inventory")
    for field in ("repository", "revision", "renderer_profile"):
        if capture.get(field) != inventory[field]:
            failures.append(f"capture {field} mismatch")
    try:
        timestamp = datetime.fromisoformat(capture.get("captured_at", "").replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError()
    except (ValueError, AttributeError, TypeError):
        failures.append("capture needs captured_at with a timezone")
    if not isinstance(capture.get("capture_method"), str) or not capture["capture_method"].strip():
        failures.append("capture needs a nonempty capture_method")
    captured_pages = capture.get("pages")
    if not isinstance(captured_pages, list) or any(not isinstance(p, dict) for p in captured_pages):
        raise ValueError("capture pages must be an array of objects")
    captured_paths = [p.get("path") for p in captured_pages]
    if captured_paths != paths:
        failures.append("capture page paths/order differ from inventory (missing, extra or duplicate page)")

    contract = {"schema_version": 1, "expressions": []} if contract is None else contract
    if not isinstance(contract, dict) or type(contract.get("schema_version")) is not int or contract["schema_version"] != 1 or not isinstance(contract.get("expressions"), list):
        raise ValueError("invalid text contract schema")
    rules: dict[tuple, dict] = {}
    known = {(p["path"], e["index"]): e for p in pages for e in p["expressions"]}
    for rule in contract["expressions"]:
        if not isinstance(rule, dict):
            raise ValueError("contract expressions must be objects")
        key = (rule.get("path"), rule.get("index"))
        if not isinstance(key[0], str) or type(key[1]) is not int or key not in known or key in rules or rule.get("source_sha256") != known[key]["source_sha256"]:
            raise ValueError("unknown, duplicate or stale expression contract")
        allowed = {"path", "index", "source_sha256", "required_text", "expected_text", "relation_override",
                   "allow_html_like_inequality", "reason", "evidence"}
        if set(rule) - allowed:
            raise ValueError("unknown contract field (contracts cannot skip checks)")
        if "expected_text" in rule and (not isinstance(rule["expected_text"], str) or not compact(rule["expected_text"])):
            raise ValueError("expected_text must be nonempty text")
        if not isinstance(rule.get("required_text", []), list) or any(
                not isinstance(v, str) or not compact(v) for v in rule.get("required_text", [])):
            raise ValueError("required_text must be an array of nonempty text")
        if "expected_text" not in rule and not rule.get("required_text"):
            raise ValueError("each expression contract needs expected_text or required_text")
        if "allow_html_like_inequality" in rule and not isinstance(rule["allow_html_like_inequality"], bool):
            raise ValueError("allow_html_like_inequality must be boolean")
        if "relation_override" in rule:
            override = rule["relation_override"]
            if not isinstance(override, dict) or any(k not in RELATION_SYMBOLS or type(v) is not int or v < 0
                                                    for k, v in override.items()):
                raise ValueError("relation_override must map known symbols to nonnegative integer counts")
        if "relation_override" in rule or rule.get("allow_html_like_inequality"):
            if not all(isinstance(rule.get(k), str) and rule[k].strip() for k in ("expected_text", "reason", "evidence")):
                raise ValueError("renderer exception requires expected_text, reason and evidence")
            exceptions.append(rule)
        rules[key] = rule

    by_path = {p.get("path"): p for p in captured_pages if isinstance(p.get("path"), str)}
    checked = 0
    for page in pages:
        path = page["path"]
        current = by_path.get(path)
        if current is None:
            continue
        boundaries.append({"path": path, "source_sha256": page["source_sha256"], "url": current.get("url"),
                           "revision": current.get("revision"), "source_expressions": len(page["expressions"]),
                           "source_spans": [{k: e[k] for k in ("index", "line_start", "line_end", "source_sha256")}
                                            for e in page["expressions"]]})
        for field, expected in (("url", page["url"]), ("revision", inventory["revision"]), ("source_sha256", page["source_sha256"])):
            if current.get(field) != expected:
                failures.append(f"{path}: captured {field} mismatch")
        if current.get("errors") != []:
            failures.append(f"{path}: renderer errors present or error evidence missing")
        hosts = current.get("math")
        if not isinstance(hosts, list):
            failures.append(f"{path}: missing math-host array")
            continue
        boundaries[-1]["captured_hosts"] = len(hosts)
        if len(hosts) != len(page["expressions"]):
            failures.append(f"{path}: {len(page['expressions'])} source expressions, {len(hosts)} captured hosts")
        for expr, host in zip(page["expressions"], hosts):
            label = f"{path}:{expr['line_start']} expression {expr['index']}"
            rule = rules.get((path, expr["index"]), {})
            if not isinstance(host, dict) or host.get("rendered") is not True or host.get("errors") != []:
                failures.append(f"{label}: missing/unrendered host or renderer-error evidence")
                continue
            if host.get("text_source") not in TEXT_SOURCES or not isinstance(host.get("text"), str) or not compact(host["text"]):
                failures.append(f"{label}: missing full accessible mathematical text/source")
                continue
            checked += 1
            text = compact(host["text"])
            expected = {k: v for k, v in rule.get("relation_override", expr["relations"]).items() if v}
            actual = dict(sorted(Counter(c for c in text if c in RELATION_SYMBOLS).items()))
            if expected != actual:
                failures.append(f"{label}: relation mismatch; expected {expected}, captured {actual}")
            for equation_label in expr["labels"]:
                if equation_label not in text:
                    failures.append(f"{label}: missing equation label {equation_label}")
            if re.search(r"<\s*[A-Za-z]", tex_body(expr["tex"])) and not rule.get("allow_html_like_inequality"):
                failures.append(f"{label}: GitHub HTML-like inequality hazard; use supported syntax or a traced exact-text exception")
            if "expected_text" in rule and compact(rule["expected_text"]) != text:
                failures.append(f"{label}: full expected_text mismatch")
            for required in rule.get("required_text", []):
                if compact(required) not in text:
                    failures.append(f"{label}: missing required_text {required!r}")
    return {"schema_version": 1, "status": "fail" if failures else "pass",
            "repository": inventory["repository"], "revision": inventory["revision"],
            "renderer_profile": inventory["renderer_profile"], "captured_at": capture.get("captured_at"),
            "capture_method": capture.get("capture_method"), "boundaries": boundaries,
            "expressions_checked": checked, "text_contracts": len(rules), "renderer_exceptions": exceptions,
            "failures": failures, "visual_review_required": True,
            "limits": "Counts, supported relations/visible labels and explicit text contracts only. No arbitrary TeX equivalence, scientific correctness, capture authentication or visual-layout certification."}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    inv = commands.add_parser("inventory", help="read math source from an exact local Git commit")
    inv.add_argument("--root", type=Path, required=True)
    inv.add_argument("--repository", required=True)
    inv.add_argument("--revision", required=True)
    inv.add_argument("--page", action="append", required=True)
    inv.add_argument("--output", type=Path, required=True)
    check = commands.add_parser("check", help="check pinned extracted capture; does not fetch or render")
    check.add_argument("--inventory", type=Path, required=True)
    check.add_argument("--capture", type=Path, required=True)
    check.add_argument("--contract", type=Path)
    check.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "inventory":
            if not SHA.fullmatch(args.revision) or len(set(args.page)) != len(args.page) or not all(safe_path(p) for p in args.page):
                raise ValueError("use an exact commit SHA and unique safe page paths")
            commit = subprocess.check_output(["git", "--no-replace-objects", "rev-parse", f"{args.revision}^{{commit}}"], cwd=args.root, text=True).strip()
            if commit != args.revision:
                raise ValueError("revision does not identify the supplied commit")
            sources = {p: subprocess.check_output(["git", "--no-replace-objects", "show", f"{commit}:{p}"], cwd=args.root).decode("utf-8") for p in args.page}
            result = make_inventory(args.repository, commit, sources)
        else:
            result = validate(read_json(args.inventory), read_json(args.capture), read_json(args.contract) if args.contract else None)
        output = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.write_text(output, encoding="utf-8")
        else:
            print(output, end="")
        return 1 if result.get("status") == "fail" else 0
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

