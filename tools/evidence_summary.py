"""Summarise existing run results and audit files; never infer missing results."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
result={'browser_runs':{},'accessibility':{},'live_test_tickets':[]}
for file in sorted((root/'evidence').glob('*-results.json')):
    data=json.loads(file.read_text())
    stats=data.get('stats',{})
    result['browser_runs'][file.name]={key:stats.get(key) for key in ('expected','unexpected','skipped','flaky','duration')}
for prefix in ['local-composer','local-final','live-third','live-fourth','live-final']:
    files=list((root/'evidence').glob(prefix+'-axe-*.json'))
    if files:
        result['accessibility'][prefix]={'pages':len(files),'violations':sum(len(json.loads(f.read_text())['violations']) for f in files)}
for file in sorted((root/'evidence').glob('live-*-test-data.json')):
    data=json.loads(file.read_text());result['live_test_tickets'].extend(data.get('tickets',[]))
(root/'evidence'/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
