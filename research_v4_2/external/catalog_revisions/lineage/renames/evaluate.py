"""Census of labeled heading renames on the PEP repository first-parent history."""
import collections
import difflib
import functools
import json
import re
import subprocess
import sys

START = "15eefc09ad1222be48d4d9956716c1c8b2cb2d5b"
END = "4434e728a7db24540d581f52e96570ca1230356e"
GIT = ["git", "-C", sys.argv[1]]
reader = subprocess.Popen(GIT + ["cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
heading = re.compile(r"^(?:\.\. _([^\n]+):\n\n)?([^\s\n][^\n]*)\n([=~^\-])\3{2,}[ \t]*$", re.M)
rights = re.compile(r"This (?:document|PEP) (?:has been|is) placed in the public domain", re.I)


@functools.lru_cache(256)
def parse(blob):
    reader.stdin.write(blob.encode() + b"\n")
    reader.stdin.flush()
    size = int(reader.stdout.readline().split()[-1])
    source = reader.stdout.read(size).decode("utf8", "replace")
    reader.stdout.read(1)
    if not rights.search(source):
        return []
    matches = list(heading.finditer(source))
    return [(m[1], m[2], m[3], source[m.end():matches[i+1].start() if i+1 < len(matches) else None])
            for i, m in enumerate(matches)]


def features(rows, mask):
    levels = list(dict.fromkeys(row[2] for row in rows))
    stack = []
    groups = collections.defaultdict(list)
    data = []
    for i, (_, title, style, body) in enumerate(rows):
        level = levels.index(style)
        while stack and stack[-1][0] >= level:
            stack.pop()
        parent = stack[-1][1] if stack else None
        groups[parent].append(i)
        clean = lambda s: mask.sub(" ", s.casefold())
        data.append((clean(title), set(re.findall(r"\w+", clean(body))[:80]), parent))
        stack.append((level, i))
    result = []
    for i, (title, words, parent) in enumerate(data):
        siblings = groups[parent]
        pos = siblings.index(i)
        near = siblings[max(0,pos-1):pos] + siblings[pos+1:pos+2]
        if parent is not None:
            near.append(parent)
        context = set(re.findall(r"\w+", " ".join(data[j][0] for j in near)))
        result.append((title, words, context))
    return result


def overlap(a, b):
    return len(a & b) / max(1, len(a | b))


def anchor(s):
    return "-".join(re.findall("[a-z0-9]+", s.lower()))


log = subprocess.check_output(GIT + ["log", "--reverse", "--first-parent", "--diff-merges=first-parent",
    "--no-renames", "--raw", "--no-abbrev", "--format=%H", START+".."+END]).decode()
rows = []
transitions = 0
for line in log.splitlines():
    if re.fullmatch("[0-9a-f]{40}", line):
        commit = line
        continue
    match = re.fullmatch(r":\d+ \d+ (\w+) (\w+) M\t((?:peps/)?pep-\d+\.rst)", line)
    if not match:
        continue
    transitions += 1
    old, new = map(parse, match.groups()[:2])
    counts = [collections.Counter(r[0] for r in side) for side in (old,new)]
    targets = {r[0]:j for j,r in enumerate(new)}
    cases = [(i,targets[k]) for i,(k,title,_,_) in enumerate(old)
             if k and counts[0][k] == counts[1][k] == 1 and title != new[targets[k]][1]]
    if not cases:
        continue
    ids = sorted({r[0].casefold() for r in old+new if r[0]}, key=lambda k:(-len(k),k))
    mask = re.compile("|".join(map(re.escape,ids)))
    a,b = (features(side,mask) for side in (old,new))
    for i,j in cases:
        title, words, context = a[i]
        scores = collections.defaultdict(list)
        for t,w,c in b:
            x = difflib.SequenceMatcher(None,title,t).ratio()
            y,z = overlap(words,w),overlap(context,c)
            for name,value in zip(("title","content","context","combined","no_title","no_content","no_context"),
                                  (x,y,z,x+y+z,y+z,x+z,x+y)):
                scores[name].append(value)
        pred = {k:max(range(len(b)),key=v.__getitem__) for k,v in scores.items()}
        pred["exact"] = next((p for p,r in enumerate(b) if anchor(r[0]) == anchor(title)),None)
        rows.append(dict(commit=commit,path=match[3],blobs=match.groups()[:2],label=old[i][0],
                         source=i,target=j,titles=[old[i][1],new[j][1]],candidates=len(b),
                         hard=anchor(old[i][1]) != anchor(new[j][1]),predictions=pred))
reader.stdin.close()
reader.wait()
print(json.dumps(dict(start=START,end=END,transitions=transitions,total=len(rows),
    hard=sum(r["hard"] for r in rows),correct={k:sum(r["predictions"][k]==r["target"] for r in rows)
    for k in rows[0]["predictions"]} if rows else {},rows=rows),indent=2))
