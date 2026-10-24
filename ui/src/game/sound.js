// Optional 8-bit cues for the scan. Off until the viewer switches it on; the choice is remembered.
const KEY = 'mrd.sound';
let ctx = null;

export function soundOn() {
  try {
    return localStorage.getItem(KEY) === '1';
  } catch {
    return false;
  }
}

export function setSoundOn(on) {
  try {
    localStorage.setItem(KEY, on ? '1' : '0');
  } catch {
    /* storage unavailable: the choice lasts for this page only */
  }
}

function tone(freq, when = 0, length = 0.09, wave = 'triangle') {
  const at = ctx.currentTime + when;
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.type = wave;
  osc.frequency.setValueAtTime(freq, at);
  gain.gain.setValueAtTime(0.0001, at);
  gain.gain.exponentialRampToValueAtTime(0.07, at + 0.012);
  gain.gain.exponentialRampToValueAtTime(0.0001, at + length);
  osc.connect(gain).connect(ctx.destination);
  osc.start(at);
  osc.stop(at + length + 0.02);
}

// One cue per game event: a blip per source, a rising note when the boss wakes, a fanfare on loot.
export function cue(kind, payload = {}) {
  if (!soundOn()) return;
  try {
    ctx ??= new (window.AudioContext || window.webkitAudioContext)();
    if (kind === 'source') tone(payload.ok ? 740 : 210, 0, 0.08, payload.ok ? 'triangle' : 'sawtooth');
    if (kind === 'agent' && payload.status === 'start') [330, 440, 550].forEach((f, i) => tone(f, i * 0.09, 0.1, 'square'));
    if (kind === 'done') [523, 659, 784, 1046].forEach((f, i) => tone(f, i * 0.1, 0.18));
  } catch {
    /* no audio device: stay silent */
  }
}
