"""Build a 720-second local TTS probe; no network or inference.

Reuses the committed eSpeak NG synthetic narration. Each minute has ten seconds
of silence, one reading, then silence. The 590s overlap starts during speech.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT / 'tests/fixtures/multimodal'


def main() -> None:
    source = MEDIA / 'release-reading.wav'
    dest = MEDIA / 'long-call.flac'
    import tempfile
    with tempfile.TemporaryDirectory(prefix='claimcheck-long-') as tmp:
        block = Path(tmp) / 'minute.wav'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(source), '-af', 'adelay=10000,apad',
                        '-t', '60', '-ac', '1', '-ar', '24000', str(block)], check=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-stream_loop', '11', '-i', str(block),
                        '-t', '720', '-c:a', 'flac', str(dest)], check=True)
    with wave.open(str(source)) as wav:
        reading_s = wav.getnframes() / wav.getframerate()
    narration = (MEDIA / 'narration.txt').read_text()
    (MEDIA / 'long-call.txt').write_text('\n\n'.join([narration.strip()] * 12) + '\n')
    record = {'duration_s': 720, 'source': source.name, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'generation': 'Committed eSpeak NG 1.53.0 offline formant narration; ffmpeg delay/pad/loop and lossless FLAC. No new model call or real speaker.',
              'speech_windows_ms': [[i * 60000 + 10000, round(i * 60000 + 10000 + reading_s * 1000)] for i in range(12)],
              'expected_financial_mentions': ['94000000000', '10%', '1.67', '12%', '12%'] * 12,
              'boundary_note': 'Second ASR upload begins at 590000ms, within the tenth reading; tests also cover exact partial overlaps and non-exact overlap retention.'}
    (MEDIA / 'long-generation.json').write_text(json.dumps(record, indent=2) + '\n')
    manifest_path = MEDIA / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    for name in ('long-call.flac', 'long-call.txt', 'long-generation.json'):
        path = MEDIA / name
        manifest['files'][name] = {'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
