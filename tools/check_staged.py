"""Fail-closed staged-file hygiene scan. Prints paths/reasons, never matched content."""
import re
import subprocess
import sys
from pathlib import PurePosixPath
paths=subprocess.check_output(['git','diff','--cached','--name-only','-z']).decode().split('\0')
problems=[]; count=0
patterns=[rb'gh[pousr]_[A-Za-z0-9]{20,}',rb'github_pat_[A-Za-z0-9_]{20,}',rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'postgres(?:ql)?(?:\+psycopg)?://[^\s:/]+:[^\s@]+@',rb'(?i)(?:authorization:\s*bearer\s+)[A-Za-z0-9._-]{20,}']
for path in filter(None,paths):
    count+=1; name=PurePosixPath(path).name
    if name.startswith('.env') or any(p in path.split('/') for p in ('.vercel','.venv','.venv314','node_modules','.cache')) or name.endswith(('.db','.sqlite','.pem','.key')):
        problems.append((path,'forbidden file category')); continue
    data=subprocess.check_output(['git','show',':'+path])
    if len(data)>5*1024*1024: problems.append((path,'file exceeds 5 MiB review limit'))
    if name.endswith(('.png','.jpg','.webp','.pdf')): continue
    if any(re.search(pattern,data) for pattern in patterns): problems.append((path,'possible credential pattern'))
print(f'Scanned {count} staged files. Findings: {len(problems)}.')
for path,reason in problems: print(path+': '+reason)
sys.exit(bool(problems))
