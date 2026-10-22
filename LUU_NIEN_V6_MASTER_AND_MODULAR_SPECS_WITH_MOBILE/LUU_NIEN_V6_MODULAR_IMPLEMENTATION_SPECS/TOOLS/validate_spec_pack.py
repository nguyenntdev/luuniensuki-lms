#!/usr/bin/env python3
"""Validate the Markdown spec pack only; NOT the Luu Nien application."""
from pathlib import Path
import re,sys,json
ROOT=Path(__file__).resolve().parent.parent
errors=[]
for md in ROOT.rglob('*.md'):
 if '99_ARCHIVE' in md.parts:continue
 s=md.read_text(encoding='utf8')
 for label,link in re.findall(r'\[([^\]\n]+)\]\(([^)]+)\)',s):
  if link.startswith(('http://','https://','mailto:','#')):continue
  target=md.parent/link.split('#',1)[0]
  if not target.exists():errors.append(f'{md.relative_to(ROOT)}: missing {link}')
 if sum(bool(re.match(r'^\s*```',line)) for line in s.splitlines())%2:
  errors.append(f'{md.relative_to(ROOT)}: unbalanced code fence')
for i in range(12):
 p=ROOT/f'03_AI_FACTORY/PHASE_P{i:02d}_TEN_RESEARCH_AGENTS.md'
 if not p.exists():errors.append(f'Missing research phase {i:02d}');continue
 roles=set(re.findall(fr'P{i:02d}-A\d\d',p.read_text()))
 if len(roles)!=10:errors.append(f'P{i:02d}: expected ten roles, got {len(roles)}')
for i in range(13):
 paths=list((ROOT/'07_DELIVERY').glob(f'W{i:02d}_10_*AGENTS.md'))
 if len(paths)!=1:errors.append(f'W{i:02d} wave missing/ambiguous');continue
 slots=set(re.findall(r'V5-T\d{3}',paths[0].read_text()))
 if len(slots)!=10:errors.append(f'W{i:02d}: expected ten tickets, got {len(slots)}')
for i in range(6):
 p=ROOT/f'04_MOBILE/WAVE_M{i:02d}.md'
 if not p.exists():errors.append(f'Mobile M{i:02d} missing');continue
 ids=set(re.findall(fr'M{i:02d}-A\d\d',p.read_text()))
 if len(ids)!=10:errors.append(f'M{i:02d}: expected ten mobile tickets, got {len(ids)}')
print(json.dumps({'spec_validation':'PASS' if not errors else 'FAIL','issues':errors,'scope':'Markdown files/links/role counts; not production tests'},ensure_ascii=False,indent=2))
sys.exit(0 if not errors else 1)
