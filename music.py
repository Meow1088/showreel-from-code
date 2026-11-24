"""Score for the showreel - every note is code. Writes out/music.wav (48 kHz stereo).
Usage: python music.py [out/music.wav]"""
import sys, wave
from pathlib import Path
import numpy as np

SR, DUR = 48000, 12.0
t = np.arange(int(SR * DUR)) / SR
rng = np.random.default_rng(5)
L = np.zeros_like(t); R = np.zeros_like(t)

def env(t0, t1, a=0.8, r=1.2):
    x = np.clip((t - t0) / a, 0, 1) * np.clip((t1 + r - t) / r, 0, 1)
    return x * x * (3 - 2 * x)

def hz(n):  # midi -> Hz
    return 440 * 2 ** ((n - 69) / 12)

def pad(notes, t0, t1, amp=0.07):
    global L, R
    e = env(t0, t1)
    for n in notes:
        f = hz(n)
        for det, side in [(-0.12, 0), (0.12, 1)]:
            ff = f * 2 ** (det / 12)
            s = sum(np.sin(2 * np.pi * ff * k * t + k) / k ** 1.6 for k in range(1, 6))
            if side == 0: L += s * e * amp
            else: R += s * e * amp

# chords: Am(add9) -> Fmaj7 -> Cmaj9/E (resolve under the title)
pad([45, 57, 60, 64, 71], 0.0, 3.4)
pad([41, 53, 57, 60, 64], 3.4, 6.5)
pad([40, 52, 55, 59, 62, 67], 6.5, 11.2, amp=0.08)

# whooshes into each cut (noise, rising envelope)
noise = rng.normal(0, 1, len(t))
nlp = np.convolve(noise, np.ones(40) / 40, mode="same")
for tc in [3.4, 6.5]:
    w = np.exp(-((t - tc) / 0.35) ** 2) * (t < tc + 0.15)
    L += nlp * w * 0.9; R += np.roll(nlp, 300) * w * 0.9

# sub hits: transition into sunrise + title reveal
for th, f0, a in [(6.5, 70, 0.55), (7.6, 55, 0.7)]:
    tt = np.clip(t - th, 0, None)
    ph = 2 * np.pi * (f0 * tt - 12 * (1 - np.exp(-tt * 6)))
    hit = np.sin(ph) * np.exp(-tt * 2.2) * (t >= th)
    L += hit * a; R += hit * a

# shimmering bells on the title (C major pentatonic arp)
for i, n in enumerate([84, 88, 91, 93, 96, 91, 88]):
    tb = 7.7 + i * 0.32
    tt = np.clip(t - tb, 0, None)
    b = (np.sin(2 * np.pi * hz(n) * tt) + 0.3 * np.sin(2 * np.pi * hz(n) * 2.01 * tt)) * np.exp(-tt * 3) * (t >= tb)
    pan = 0.5 + 0.35 * np.sin(i * 1.7)
    L += b * 0.06 * (1 - pan); R += b * 0.06 * pan

# soft surf under the ocean shot
surf = np.convolve(rng.normal(0, 1, len(t)), np.ones(400) / 400, mode="same") * 6
swell = 0.6 + 0.4 * np.sin(2 * np.pi * t / 2.7)
L += surf * swell * env(6.6, 11.0, 1.5, 1.0) * 0.12
R += np.roll(surf, 2400) * swell * env(6.6, 11.0, 1.5, 1.0) * 0.12

# simple stereo reverb: feedback comb taps
def verb(x, delays=(1931, 2713, 3571, 4447), g=0.35):
    y = x.copy()
    for d in delays:
        y[d:] += x[:-d] * g; g *= 0.8
    return y
L, R = verb(L), verb(R, (2111, 2903, 3767, 4621))

mix = np.stack([L, R], 1)
mix *= np.clip((DUR - t) / 0.7, 0, 1)[:, None] * np.clip(t / 0.3, 0, 1)[:, None]
mix = np.tanh(mix / np.percentile(np.abs(mix), 99.7) * 0.8) * 0.89
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "out" / "music.wav"
OUT.parent.mkdir(parents=True, exist_ok=True)
with wave.open(str(OUT), "wb") as wv:
    wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR)
    wv.writeframes((mix * 32767).astype("<i2").tobytes())
print("written", OUT, mix.shape)
