#!/bin/bash
set -e

echo '=== [1] quick health probes ==='
curl -sS -o /dev/null -w 'GET /api/projects  -> HTTP %{http_code} (%{time_total}s)\n' http://127.0.0.1:8001/api/projects
curl -sS -o /dev/null -w 'GET /api/settings  -> HTTP %{http_code} (%{time_total}s)\n' http://127.0.0.1:8001/api/settings
echo

echo '=== [2] count projects + dump one with characters ==='
curl -sS http://127.0.0.1:8001/api/projects > /tmp/projects.json
python3 -c "
import json
d=json.load(open('/tmp/projects.json'))
print('total projects:', len(d))
for p in d[:5]:
  print('  ', p.get('id'), '|', p.get('title','?'), '| chars:', len(p.get('characters',[])), '| scenes:', len(p.get('scenes',[])), '| shots(est):', sum(len(s.get('shots',[])) for s in p.get('scenes',[])))
"
echo

echo '=== [3] pick a project with characters + at least one scene ---'
python3 <<'PYEOF'
import json
d=json.load(open('/tmp/projects.json'))
candidates = [p for p in d if p.get('characters') and any(s.get('shots') for s in p.get('scenes',[]))]
if not candidates:
  candidates = [p for p in d if p.get('characters') and p.get('scenes')] or (d[:1] if d else [])
print('picked:', candidates[0].get('id') if candidates else 'NONE')
if candidates:
  p = candidates[0]
  sc = next((s for s in p['scenes'] if s.get('shots')), p['scenes'][0] if p['scenes'] else None)
  sh = sc['shots'][0] if sc and sc.get('shots') else None
  payload = {'sceneId': sc.get('id','') if sc else '', 'shotId': sh.get('id','') if sh else ''}
  print('  scene:', payload['sceneId'], '  shot:', payload['shotId'])
  open('/tmp/shot_payload.json','w').write(json.dumps(payload))
  open('/tmp/project_id.txt','w').write(p['id'])
PYEOF
cat /tmp/project_id.txt 2>/dev/null
echo
cat /tmp/shot_payload.json 2>/dev/null
echo

echo '=== [4] POST Smart Shot generate ==='
PID=$(cat /tmp/project_id.txt)
PAYLOAD=$(cat /tmp/shot_payload.json)
curl -sS -X POST -H 'Content-Type: application/json' -d "$PAYLOAD" \
  "http://127.0.0.1:8001/api/projects/$PID/shots/generate" \
  -o /tmp/shot_resp.json -w 'HTTP %{http_code} -- time %{time_total}s -- bytes %{size_download}\n'
echo '--- response (head) ---'
head -c 1200 /tmp/shot_resp.json
echo

echo '=== [5] extract image url from response and curl it ==='
IMG=$(python3 -c "
import json
try:
  d=json.load(open('/tmp/shot_resp.json'))
  for k in ('imageUrl','image','url','image_url'):
    if isinstance(d.get(k),str): print(d[k]); break
  else:
    for k in ('result',):
      v=d.get(k)
      if isinstance(v,dict):
        for kk in ('imageUrl','image','url'):
          if isinstance(v.get(kk),str): print(v[kk]); break
except: pass
")
echo "  resolved image url: $IMG"
if [ -n "$IMG" ]; then
  if [[ "$IMG" != http* ]]; then IMG="http://127.0.0.1:8001$IMG"; fi
  curl -sS -o /tmp/shot.png -w 'GET image HTTP %{http_code} -- type %{content_type} -- bytes %{size_download}\n' "$IMG"
  file /tmp/shot.png
fi
