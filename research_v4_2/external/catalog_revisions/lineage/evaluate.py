"""Evaluate heading relocation within the same PEP path across two Git revisions."""
import collections
import difflib
import json
import re
import subprocess
import sys

OLD = "828523ad82ea4185d55a34ca06081f2eae02118c"
NEW = "152a687059b899e69f9e2a866c331c3cb86949e9"
HEADING = re.compile(r"^(?:\.\. _([^\n]+):\n\n)?([^\s\n][^\n]*)\n([=~^-])\3{2,}[ \t]*$", re.M)
RIGHTS = re.compile(r"This (?:document|PEP) (?:has been|is) placed in the public domain", re.I)


def git(*args):
    return subprocess.check_output(["git", "-C", sys.argv[1], *args]).decode()


def sections(source):
    matches = list(HEADING.finditer(source))
    rows = []
    for i, match in enumerate(matches):
        title = match[2]
        body = source[match.end():matches[i+1].start() if i+1 < len(matches) else None]
        words = re.findall(r"\w+", re.sub(r"^\.\. .*", "", body, flags=re.M).casefold())
        rows.append((match[1], title, set(words[:80])))
    return rows


def slug(title):
    return "-".join(re.findall(r"[a-z0-9]+", title.lower()))


def main():
    paths = [set(git("ls-tree", "-r", "--name-only", rev, "peps").splitlines())
             for rev in (OLD, NEW)]
    results = []
    for path in sorted(paths[0] & paths[1]):
        if not re.fullmatch(r"peps/pep-\d+\.rst", path):
            continue
        sources = [git("show", f"{rev}:{path}") for rev in (OLD, NEW)]
        if sources[0] == sources[1] or not all(RIGHTS.search(s) for s in sources):
            continue
        old, new = map(sections, sources)
        for i, (label, title, words) in enumerate(old):
            if not label or sum(r[0] == label for r in old) != 1:
                continue
            targets = [j for j, row in enumerate(new) if row[0] == label]
            exact = [j for j, row in enumerate(new) if slug(row[1]) == slug(title)]
            text = [difflib.SequenceMatcher(None, title.casefold(), r[1].casefold()).ratio()
                    for r in new]
            context = [score + len(words & r[2]) / max(1, len(words | r[2]))
                       for score, r in zip(text, new)]
            results.append(dict(path=path, old_index=i, label=label, title=title,
                                targets=targets, exact=next(iter(exact), None),
                                text=max(range(len(new)), key=text.__getitem__, default=None),
                                context=max(range(len(new)), key=context.__getitem__, default=None),
                                target_title=new[targets[0]][1] if len(targets)==1 else None))
    eligible = [r for r in results if len(r["targets"]) == 1]
    print(json.dumps(dict(total=len(results), recoverable=len(eligible),
                          correct={k:sum(r[k]==r["targets"][0] for r in eligible)
                                   for k in ("exact","text","context")}, rows=results), indent=2))


if __name__ == "__main__":
    main()
