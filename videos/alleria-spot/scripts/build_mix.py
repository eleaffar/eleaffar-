"""Build the SFX layer for the HyperFrames composition.

- Levels every sample (bundled media-use library + a few custom cartoon cues the
  library lacks) to the same perceived loudness, so quiet clicks are not buried.
- Maps each animation-synced event in sfx-events.json to a sample.
- Bakes the dense letter-by-letter ticks into one stem (hundreds of 30 ms hits).
- Writes the <audio> clips + mix buses into index.html between <!--AUDIO--> markers.
- Writes a reference offline mix (renders/mix-check.wav) for level verification.
"""
import json, os, subprocess, wave
import numpy as np

SR = 48000
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SFX_IN = os.path.join(ROOT, 'assets/sfx')
OUT = os.path.join(ROOT, 'assets/sfx-mix')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(11)


def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def save(path, x):
    x = np.clip(x, -1, 1)
    st = np.stack([x, x], 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


def db(x): return 20 * np.log10(max(x, 1e-9))


def level(x, target_rms_db=-13.0, ceiling_db=-1.0):
    """Equal perceived loudness: loudest 50 ms window to target RMS, soft ceiling."""
    x = x / (np.max(np.abs(x)) + 1e-9)
    w = int(.05 * SR)
    if len(x) > w:
        sq = np.convolve(x ** 2, np.ones(w) / w, 'valid')
        win_rms = np.sqrt(sq.max())
    else:
        win_rms = np.sqrt(np.mean(x ** 2))
    g = 10 ** ((target_rms_db - db(win_rms)) / 20)
    g = min(g, 10 ** (12 / 20))
    y = x * g
    c = 10 ** (ceiling_db / 20)
    return np.tanh(y / c) * c


# ── custom cues the 21-file library does not have (cartoon physics for the mascot)
def tt(d): return np.arange(int(SR * d)) / SR
def env(d, tau, att=.002): t = tt(d); return np.minimum(1, t / att) * np.exp(-t / tau)
def sweep(f0, f1, d, c=1.0):
    t = tt(d); f = f0 * (f1 / f0) ** ((t / d) ** c); return np.sin(2 * np.pi * np.cumsum(f) / SR)
def band(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))

CUSTOM = {
    'boing': lambda: np.sin(2 * np.pi * np.cumsum(220 + 160 * np.exp(-tt(.45) / .15) * (1 + .5 * np.sin(2 * np.pi * 13 * tt(.45)))) / SR) * env(.45, .16),
    'fall': lambda: sweep(1500, 520, .42) * np.minimum(1, tt(.42) / .04) * np.exp(-tt(.42) / .6),
    'drip': lambda: sweep(520, 1500, .11, 2.5) * env(.11, .045),
    'pen': lambda: band(rng.standard_normal(int(.82 * SR)), 1500, 6000) * (.45 + .55 * np.sin(2 * np.pi * 17 * tt(.82)) ** 2) * np.minimum(1, tt(.82) / .03) * np.minimum(1, (.82 - tt(.82)) / .05),
    'wink': lambda: np.concatenate([sweep(1100, 1500, .06) * env(.06, .025), sweep(1700, 2500, .09) * env(.09, .035)]),
}

samples = {}
for f in sorted(os.listdir(SFX_IN)):
    if f.endswith('.mp3'):
        samples[f[:-4]] = load(os.path.join(SFX_IN, f))
for k, fn in CUSTOM.items():
    samples['custom-' + k] = fn()

leveled, dur = {}, {}
for k, x in samples.items():
    # long beds (riser / cinematic whoosh) sit a little lower than one-shot hits
    tgt = -16.0 if k in ('riser', 'whoosh-cinematic') else -12.0
    if k in ('impact-bass-1', 'impact-bass-2'): tgt = -11.0
    y = level(x, tgt)
    leveled[k] = y; dur[k] = len(y) / SR
    save(os.path.join(OUT, k + '.wav'), y)

# ── event → (sample, volume, media_start, max_duration)
MAP = {
    'click': [('click', 1.0)], 'grab': [('click-soft', .9)], 'snap': [('click', .9)],
    'pop': [('pop', 1.0)], 'land': [('pop', .7)], 'blip': [('pop', .8)],
    'whoosh': [('whoosh', 1.0)], 'swish': [('whoosh-short', .8)], 'slide': [('whoosh-short', .8)],
    'flip': [('whoosh-short', .85)], 'scan': [('whoosh-short', .6)], 'fold': [('whoosh', 1.0)],
    'curtain': [('whoosh-cinematic', 1.0, 0, 1.6)],
    'split': [('whoosh-short', .9), ('pop', .9, 0, None, .15)],
    'drip': [('custom-drip', 1.0)], 'ding': [('ping', 1.0)], 'chime': [('chime', 1.0)],
    'shimmer': [('sparkle', 1.0)], 'burst': [('sparkle', 1.0), ('pop', 1.0)], 'rise': [('ping', .8)],
    'riser': [('riser', 1.0, 9.03, 1.0)], 'charge': [('riser', 1.0, 8.63, 1.4)],
    'boom': [('impact-bass-2', 1.0)], 'stamp': [('impact-bass-1', 1.0)], 'hit': [('impact-bass-1', 1.0)],
    'bubble': [('notification', .9)], 'pen': [('custom-pen', .9)], 'fall': [('custom-fall', .8)],
    'boing': [('custom-boing', 1.0)], 'wink': [('custom-wink', 1.0), ('sparkle', .7)],
}

events = json.load(open(os.path.join(ROOT, 'sfx-events.json')))
clips, letters = [], []
for t, kind, g in events:
    if kind == 'key' or (kind == 'tick' and g < .5):   # typing + letter-by-letter captions
        letters.append((t, .55 if kind == 'key' else .42))
        continue
    if kind == 'tick':                                   # keyframe pops on the timeline
        clips.append(('click-soft', t, 1.0, 0, None)); continue
    for m in MAP[kind]:
        name, vol = m[0], m[1]
        ms = m[2] if len(m) > 2 else 0
        md = m[3] if len(m) > 3 else None
        off = m[4] if len(m) > 4 else 0
        clips.append((name, t + off, vol * min(1.0, .55 + .45 * g), ms, md))

# dedupe identical sample hits within 30 ms
clips.sort(key=lambda c: c[1])
ded = []
for c in clips:
    if ded and ded[-1][0] == c[0] and abs(ded[-1][1] - c[1]) < .03:
        continue
    ded.append(c)
clips = ded

# letters stem
N = int(SR * 30)
stem = np.zeros(N)
kp = leveled['key-press']
for t, v in letters:
    i = int(t * SR); n = min(len(kp), N - i)
    if n > 0: stem[i:i + n] += kp[:n] * v
stem = np.tanh(stem / .89) * .89
save(os.path.join(OUT, 'letters-stem.wav'), stem)

# ── music duck lane: -5 dB under every prominent hit (music stays audible)
hits = sorted(set(round(c[1], 3) for c in clips if c[2] >= .8))
pts = [{"t": 0, "v": 0}]
for t in hits:
    a, b, r = max(0, t - .02), t + .04, t + .28
    if pts and a <= pts[-1]["t"]:
        pts[-1] = {"t": pts[-1]["t"], "v": -5}
        pts.append({"t": round(r, 3), "v": 0}); continue
    pts += [{"t": round(a, 3), "v": 0}, {"t": round(b, 3), "v": -5}, {"t": round(r, 3), "v": 0, "curve": .3}]
# collapse to monotonic t and cap at 512
clean = []
for p in pts:
    if clean and p["t"] <= clean[-1]["t"]:
        clean[-1]["v"] = min(clean[-1]["v"], p["v"]); continue
    clean.append(p)
pts = clean[:512]

def attr(o): return json.dumps(o, separators=(',', ':')).replace('&', '&amp;').replace('"', '&quot;')

music_chain = {"version": 1, "nodes": [
    {"type": "peaking", "id": "n1", "label": "Room for SFX", "params": {"frequency": 2800, "gain": -4, "q": 0.9}},
    {"type": "gain", "id": "duck", "label": "Duck under SFX", "params": {"gain": 0}},
    {"type": "limiter", "id": "n3", "label": "Ceiling", "params": {"limit": -1, "attack": 5, "release": 80, "level_out": 0}}]}
music_auto = {"version": 1, "lanes": [{"target": "fx.duck.gain", "points": pts}]}
sfx_chain = {"version": 1, "nodes": [
    {"type": "compressor", "id": "n1", "label": "Glue", "params": {"threshold": -16, "ratio": 3, "attack": 2, "release": 120, "makeup": 2}},
    {"type": "limiter", "id": "n2", "label": "Ceiling", "params": {"limit": -1, "attack": 1, "release": 60, "level_out": 0}}]}

lines = ['<!--AUDIO-->',
         f'<hf-audio-group id="music" data-label="Musica" data-volume="0.5" data-fx-chain="{attr(music_chain)}" data-automation="{attr(music_auto)}"></hf-audio-group>',
         f'<hf-audio-group id="sfx" data-label="Effetti sonori" data-volume="1" data-fx-chain="{attr(sfx_chain)}"></hf-audio-group>',
         '<audio id="bgm" src="assets/bgm/alleria-bed.wav" data-start="0" data-duration="30" data-track-index="20" data-volume="1" data-audio-group="music"></audio>',
         '<audio id="sfx-letters" src="assets/sfx-mix/letters-stem.wav" data-start="0" data-duration="30" data-track-index="21" data-volume="0.85" data-audio-group="sfx"></audio>']
track_end = []  # greedy lanes: no two clips overlap on one track
for i, (name, t, vol, ms, md) in enumerate(clips):
    d = md if md else min(dur[name], 2.6)
    d = round(min(d, 30 - t), 3)
    if d <= 0: continue
    lane = next((k for k, e in enumerate(track_end) if e <= t), None)
    if lane is None:
        track_end.append(0); lane = len(track_end) - 1
    track_end[lane] = t + d
    extra = f' data-media-start="{ms}"' if ms else ''
    lines.append(f'<audio id="sfx-{i:03d}" src="assets/sfx-mix/{name}.wav" data-start="{t:.3f}" data-duration="{d}"{extra} data-track-index="{22 + lane}" data-volume="{vol:.2f}" data-audio-group="sfx"></audio>')
lines.append('<!--/AUDIO-->')

p = os.path.join(ROOT, 'index.html')
html = open(p).read()
a, b = html.index('<!--AUDIO-->'), html.index('<!--/AUDIO-->') + len('<!--/AUDIO-->')
open(p, 'w').write(html[:a] + '\n'.join(lines) + html[b:])

# ── reference offline mix for level verification (approximates the buses)
bed = load(os.path.join(ROOT, 'assets/bgm/alleria-bed.wav'))[:N]
bed = np.pad(bed, (0, N - len(bed)))
duck = np.ones(N)
tp = [q["t"] for q in pts]; vp = [q["v"] for q in pts]
duck = 10 ** (np.interp(np.arange(N) / SR, tp, vp) / 20)
music = bed * .5 * duck
sfx = stem * .85
for name, t, vol, ms, md in clips:
    x = leveled[name][int(ms * SR):]
    d = md if md else min(dur[name], 2.6)
    x = x[:int(d * SR)]
    i = int(t * SR); n = min(len(x), N - i)
    if n > 0: sfx[i:i + n] += x[:n] * vol
os.makedirs(os.path.join(ROOT, 'renders'), exist_ok=True)
save(os.path.join(ROOT, 'renders/mix-check.wav'), np.tanh((music + sfx) / .95) * .95)

# audibility report: SFX hit peak vs music RMS around it
w = int(.05 * SR)
ratios = []
for name, t, vol, ms, md in clips:
    i = int(t * SR)
    seg_s = sfx[i:i + int(.12 * SR)]; seg_m = music[max(0, i - w):i + int(.12 * SR)]
    if len(seg_s) and len(seg_m):
        ratios.append(db(np.max(np.abs(seg_s))) - db(np.sqrt(np.mean(seg_m ** 2))))
ratios = np.array(ratios)
print(f'clips: {len(clips)} + letters stem ({len(letters)} hits) + bgm; duck points: {len(pts)}')
print(f'SFX peak over music RMS (dB): min {ratios.min():.1f} · median {np.median(ratios):.1f} · 10th pct {np.percentile(ratios, 10):.1f}')
