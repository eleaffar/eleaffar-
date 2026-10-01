# Original 120 BPM music bed (offline; HeyGen BGM retrieval unavailable without sign-in)
import numpy as np, json, wave, os
SR = 48000
DUR = 30.0
N = int(SR * DUR)
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
rng = np.random.default_rng(3)

def tt(d): return np.arange(int(SR * d)) / SR
def mhz(m): return 440.0 * 2 ** ((m - 69) / 12)
def put(buf, t0, x, g=1.0):
    i = int(round(t0 * SR))
    if i >= len(buf): return
    if i < 0: x = x[-i:]; i = 0
    n = min(len(x), len(buf) - i)
    buf[i:i + n] += x[:n] * g

def band(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))

def noise(d): return rng.standard_normal(int(SR * d))
def env_exp(d, tau, att=0.002):
    t = tt(d); return np.minimum(1, t / att) * np.exp(-t / tau)
def sweep_sine(f0, f1, d, curve=1.0):
    t = tt(d); p = (t / d) ** curve; f = f0 * (f1 / f0) ** p
    return np.sin(2 * np.pi * np.cumsum(f) / SR)
def saw(f, d, fc=3000, voices=(0,), amp_env=None):
    t = tt(d); out = np.zeros_like(t)
    for dt in voices:
        ff = f * 2 ** (dt / 1200); ph = rng.random() * 2 * np.pi
        k = np.arange(1, int(min(12000, fc * 3) / ff) + 1)
        w = np.exp(-(k * ff / fc) ** 2) / k
        for kk, ww in zip(k, w):
            if ww < 1e-3: break
            out += ww * np.sin(2 * np.pi * kk * ff * t + kk * ph)
    out /= len(voices)
    return out * (amp_env if amp_env is not None else 1)

def reverb(x, secs=1.6, mix=0.25):
    ir = rng.standard_normal(int(SR * secs)) * np.exp(-np.arange(int(SR * secs)) / (SR * secs / 6))
    ir = band(ir, 200, 9000); ir /= np.sqrt(np.sum(ir ** 2))
    L = len(x) + len(ir)
    y = np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[:len(x)]
    return x * (1 - mix) + y * mix * 0.6

# ───────────── music
BPM = 120; BEAT = 60 / BPM; BAR = 4 * BEAT
CH = [(48, [60, 64, 67, 72]), (43, [59, 62, 67, 74]), (45, [60, 64, 69, 72]), (41, [60, 65, 69, 72])]
drums = np.zeros(N); bass = np.zeros(N); chords = np.zeros(N); arp = np.zeros(N); lead = np.zeros(N); pad = np.zeros(N)

def kick():
    d = .42; t = tt(d); f = 45 + 110 * np.exp(-t / .035)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .16)
    x[:int(.004 * SR)] += band(noise(.004), 1000, 8000) * .4
    return np.tanh(x * 1.6)
def clap():
    x = np.zeros(int(.3 * SR)); n = band(noise(.3), 900, 6000)
    for o in (0, .011, .022):
        e = env_exp(.3, .012 if o < .02 else .07); m = len(n) - int(o * SR)
        put(x, o, n[:m] * e[:m])
    return x * .55
def hat(d=.05): return band(noise(.12), 7000, 16000)[:int(.12 * SR)] * env_exp(.12, d) * .32
K, CL, HC, HO = kick(), clap(), hat(.018), hat(.07)

kicks = []
def in_drop(t): return 27.0 <= t < 28.0
for b in range(int(DUR / BEAT) + 1):
    t = b * BEAT
    if t >= DUR: break
    full = t >= 1.0 and not in_drop(t) and t < 29.5
    if full or (t >= 28.0 and t < 29.5):
        put(drums, t, K, .95); kicks.append(t)
    if full and b % 2 == 1: put(drums, t, CL, .8)
    if t >= .0 and not in_drop(t) and t < 29.6:
        put(drums, t + BEAT / 2, HO, .38 if t >= 1 else .22)
        put(drums, t + BEAT / 4, HC, .22); put(drums, t + 3 * BEAT / 4, HC, .2)
# snare roll builds
for t0, t1 in ((12.5, 13.0), (25.5, 26.0)):
    n = 16
    for i in range(n):
        put(drums, t0 + (t1 - t0) * i / n, CL, .25 + .5 * i / n)
# crash at sections
crash = band(noise(1.8), 4000, 15000) * env_exp(1.8, .5) * .35
for t in (1.0, 14.0, 26.0): put(drums, t, crash)

for bar in range(16):
    t0 = bar * BAR
    root, ch = CH[bar % 4]
    for e in range(8):  # offbeat pumping bass + root on downbeats
        tb = t0 + e * BEAT / 2
        if tb >= DUR or in_drop(tb): continue
        if tb < 1.0: continue
        note = root + (12 if e % 2 else 0)
        d = .2
        x = saw(mhz(note), d, fc=700 if tb < 26 else 900, voices=(-6, 6)) * env_exp(d, .12, .004)
        x += np.sin(2 * np.pi * mhz(note - 12 if e % 2 == 0 else note) * tt(d)) * env_exp(d, .15, .004) * .8
        put(bass, tb, x, .55)
    # chord stabs (syncopated)
    for pos in (0, 1.5, 2.5, 3.5) if bar % 2 == 0 else (0, .75, 1.5, 2.5, 3.25):
        ts = t0 + pos * BEAT
        if ts >= DUR or in_drop(ts) or ts < 1.0 or ts >= 28.0: continue
        d = .22
        x = sum(saw(mhz(m), d, fc=3200, voices=(-14, 0, 14)) for m in ch) / 4 * env_exp(d, .1, .003)
        put(chords, ts, x, .5)
    # pad
    if t0 < 28:
        d = BAR + .2
        x = sum(saw(mhz(m - 12), d, fc=1200, voices=(-9, 9)) for m in ch[:3]) / 3
        a = np.minimum(1, tt(d) / .3) * np.minimum(1, (d - tt(d)) / .2)
        put(pad, t0, x * a, .16)
    # arpeggio 16ths
    seq = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 12, ch[1] + 12, ch[3] + 12, ch[2] + 24]
    for s in range(16):
        ta = t0 + s * BEAT / 4
        if ta >= 28.0 or in_drop(ta): continue
        m = seq[s % 8]; d = .14
        x = saw(mhz(m), d, fc=2600 + 1400 * np.sin(ta * .4) ** 2, voices=(0,)) * env_exp(d, .05, .002)
        x += np.sin(2 * np.pi * mhz(m) * tt(d)) * env_exp(d, .06, .002) * .5
        put(arp, ta, x, .15 if ta >= 1 else .3)

# lead hook (bars from 14s to 26s)
HOOK = [(0, 76, .5), (.5, 79, .25), (.75, 81, .25), (1, 79, .5), (1.5, 76, .5), (2, 74, .5), (2.75, 76, .25), (3, 72, 1)]
for rep in range(6):
    t0 = 14.0 + rep * BAR
    if t0 >= 26: break
    for p, m, l in HOOK:
        d = l * BEAT * .95; t = tt(d)
        vib = 1 + .004 * np.sin(2 * np.pi * 5.5 * t) * np.minimum(1, t / .15)
        ph = 2 * np.pi * np.cumsum(mhz(m + (-12 if rep % 2 else 0) + 12) * vib) / SR
        x = (np.sign(np.sin(ph)) * .35 + np.sin(ph) * .65)
        x = band(x, 100, 5000) * np.minimum(1, t / .01) * np.minimum(1, (d - t) / .03) * np.exp(-t / .6)
        put(lead, t0 + p * BEAT, x, .16)

# final chord (28–30) and intro riser
final_ch = [48, 60, 64, 67, 72, 76]
d = 2.0
x = sum(saw(mhz(m), d, fc=2400, voices=(-12, 0, 12)) for m in final_ch) / 6 * np.minimum(1, tt(d) / .05) * np.exp(-tt(d) / 1.4)
put(chords, 28.0, x, .5)
put(chords, 29.6, sum(saw(mhz(m), .4, fc=3500, voices=(-12, 12)) for m in final_ch) / 6 * env_exp(.4, .25), .6)

# sidechain
sc = np.ones(N); t = np.arange(N) / SR
for k in kicks:
    i = int(k * SR); L = int(.3 * SR); seg = 1 - .65 * np.exp(-np.arange(L) / (SR * .09))
    sc[i:i + L] = np.minimum(sc[i:i + L], seg[:max(0, min(L, N - i))])
# drop filter: muffle 27–28 by attenuating
dropenv = np.ones(N); dropenv[(t >= 27.0) & (t < 28.0)] = .55
music = drums * 1.0 + (bass * 1.0 + chords * .9 + pad + arp) * sc + lead * sc
music = music * dropenv
music = reverb(music, 1.4, .18)
# fade tail
music *= np.where(t > 29.75, np.clip((30.0 - t) / .25, 0, 1), 1)


music = music / np.max(np.abs(music)) * 0.89
st = np.stack([music, np.concatenate([np.zeros(12), music[:-12]])], 1)
with wave.open(os.path.join(HERE, 'assets/bgm/alleria-bed.wav'), 'wb') as wv:
    wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes((st * 32767).astype(np.int16).tobytes())
print('bed ok')
