"""Run inside the local image with --read-only --network none and dummy token."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

assert sys.version_info[:2] == (3, 12)
assert os.getuid() == 10001
try:
    Path('/app/rootfs-write-test').write_text('test')
except OSError:
    pass
else:
    raise AssertionError('root filesystem must be read-only')
child = subprocess.Popen([sys.executable, '-m', 'server.live.server'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def get(path, *, authorized=True, body=None):
    headers = {'X-Live-Origin-Token': 'offline-container-token'} if authorized else {}
    if body is not None:
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request('http://127.0.0.1:8080' + path, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)

try:
    for _ in range(100):
        try:
            assert get('/healthz') == (200, {'ok': True})
            break
        except urllib.error.URLError:
            time.sleep(.1)
    else:
        raise AssertionError('server did not become healthy')
    assert get('/healthz', authorized=False) == (401, {'error': 'origin_rejected', 'demo': 'data/live-demo.json'})
    status, budget = get('/api/budget')
    assert status == 200 and budget['daily_remaining_usd'] == 3
    assert get('/api/check', body=b'{"text":"Apple FY2026 revenue was $10 billion"}')[0] == 503
    assert get('/api/check', body=b'x' * 4097)[0] == 400
    assert get('/unknown')[0] == 404
finally:
    child.terminate()
    stdout, stderr = child.communicate(timeout=10)
    assert not stdout and not stderr, (stdout, stderr)
assert Path('/data/ledger.sqlite3').is_file()
print('PASS Python 3.12 amd64 container: UID 10001, read-only root, network none, authenticated health/budget, disabled checks, body cap, unknown route, silent logs, persistent ledger')
