"""Lightweight MFCC-mean similarity screening; a proxy, not speaker identification.

Use librosa when installed. The stdlib fallback keeps this command/test usable offline
without adding large numerical packages to the pinned media environment.
"""
from __future__ import annotations

import cmath
import math
import wave
from pathlib import Path

from pipeline import BuildError

RATE, FFT, HOP, MELS, COEFFS = 16000, 512, 256, 26, 14


def pcm(path: Path) -> list[float]:
    try:
        with wave.open(str(path), 'rb') as wav:
            channels, width, rate = wav.getnchannels(), wav.getsampwidth(), wav.getframerate()
            raw = wav.readframes(wav.getnframes())
            if wav.getcomptype() != 'NONE' or width not in (1, 2, 3, 4):
                raise BuildError(f'{path}: voicecheck needs uncompressed PCM WAV.')
    except (OSError, wave.Error) as error:
        raise BuildError(f'Cannot read voicecheck audio {path}: {error}') from error
    samples = []
    for i in range(0, len(raw), width * channels):
        values = []
        for c in range(channels):
            b = raw[i+c*width:i+(c+1)*width]
            values.append((b[0]-128)/128 if width == 1 else int.from_bytes(b, 'little', signed=True)/2**(width*8-1))
        samples.append(sum(values)/channels)
    if len(samples) < rate / 10 or max(map(abs, samples), default=0) < 1e-6:
        raise BuildError(f'{path}: voicecheck requires at least 0.1 s of non-silent audio.')
    if rate != RATE:
        count = int(len(samples)*RATE/rate)
        out = []
        for i in range(count):
            at = i*rate/RATE; low = int(at); high = min(low+1, len(samples)-1)
            out.append(samples[low] + (samples[high]-samples[low])*(at-low))
        samples = out
    return samples


def fft(values: list[float]) -> list[complex]:
    out = [complex(v) for v in values]
    j = 0
    for i in range(1, len(out)):
        bit = len(out) >> 1
        while j & bit:
            j ^= bit; bit >>= 1
        j ^= bit
        if i < j:
            out[i], out[j] = out[j], out[i]
    length = 2
    while length <= len(out):
        root = cmath.exp(-2j*math.pi/length)
        for start in range(0, len(out), length):
            w = 1+0j
            for k in range(length//2):
                a, b = out[start+k], w*out[start+k+length//2]
                out[start+k], out[start+k+length//2] = a+b, a-b
                w *= root
        length *= 2
    return out


def mfcc_mean(samples: list[float], backend: str = 'auto') -> tuple[list[float], str]:
    if backend not in ('auto', 'python', 'librosa'):
        raise BuildError(f'Unknown voicecheck backend: {backend}')
    if backend != 'python':
        try:
            import librosa
            import numpy as np
        except ImportError:
            if backend == 'librosa':
                raise BuildError('librosa is not installed; use the offline Python MFCC fallback.')
        else:
            features = librosa.feature.mfcc(y=np.asarray(samples), sr=RATE, n_mfcc=COEFFS,
                                           n_fft=FFT, hop_length=HOP, n_mels=MELS, htk=True)
            return features[1:].mean(axis=1).tolist(), 'librosa'
    # HTK mel bank, Hann window, log-mel energy, orthonormal DCT-II; omit energy C0.
    mel_top = 2595*math.log10(1+(RATE/2)/700)
    hz = [700*(10**(mel_top*i/(MELS+1)/2595)-1) for i in range(MELS+2)]
    frequencies = [i*RATE/FFT for i in range(FFT//2+1)]
    bank = [[max(0., min((f-left)/(mid-left), (right-f)/(right-mid)))
             for f in frequencies] for left,mid,right in zip(hz,hz[1:],hz[2:])]
    window = [.5-.5*math.cos(2*math.pi*i/FFT) for i in range(FFT)]
    means = [0.]*(COEFFS-1); count = 0
    for start in range(0, len(samples)-FFT+1, HOP):
        frame = samples[start:start+FFT]
        if sum(v*v for v in frame)/FFT < 1e-10:
            continue
        spectrum = fft([v*w for v,w in zip(frame,window)])
        power = [abs(v)**2 for v in spectrum[:FFT//2+1]]
        logs = [10*math.log10(max(1e-10, sum(w*p for w,p in zip(weights,power)))) for weights in bank]
        logs = [max(max(logs)-80, v) for v in logs]
        for k in range(1, COEFFS):
            means[k-1] += math.sqrt(2/MELS)*sum(v*math.cos(math.pi*k*(i+.5)/MELS) for i,v in enumerate(logs))
        count += 1
    if not count:
        raise BuildError('No non-silent analysis frames in voicecheck clip.')
    return [v/count for v in means], 'python-mfcc'


def cosine(a: list[float], b: list[float]) -> float:
    norm = math.sqrt(sum(v*v for v in a)*sum(v*v for v in b))
    if norm < 1e-12:
        raise BuildError('Degenerate MFCC vector; cannot compare silent/flat audio.')
    return max(-1., min(1., sum(x*y for x,y in zip(a,b))/norm))


def compare_clips(paths: list[Path], threshold: float = .85, backend: str = 'auto') -> dict:
    if not math.isfinite(threshold) or not -1 <= threshold <= 1:
        raise BuildError('Voicecheck threshold must be finite, between -1 and 1.')
    if len(paths) < 2:
        raise BuildError('voicecheck requires at least two clips.')
    vectors, actual = [], None
    for path in paths:
        vector, actual = mfcc_mean(pcm(path), backend)
        vectors.append(vector)
    pairs = [dict(a=str(paths[i]), b=str(paths[j]), similarity=cosine(vectors[i], vectors[j]))
             for i in range(len(paths)) for j in range(i+1, len(paths))]
    minimum = min(p['similarity'] for p in pairs)
    return dict(method='MFCC mean (C1–C13) cosine', backend=actual, threshold=threshold,
                min_pairwise_similarity=minimum, passed=minimum >= threshold, pairs=pairs,
                note='Screening proxy only. Listen to all cloned narration clips during host review.')
