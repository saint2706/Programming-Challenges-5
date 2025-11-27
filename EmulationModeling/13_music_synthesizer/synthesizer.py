"""
Simple music synthesizer using NumPy and PyAudio.

Generates basic waveforms (sine, square, sawtooth), applies an ADSR envelope,
combines multiple oscillators, and can play a small melody sequence.

Running this module will attempt to play a short demonstration melody.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

from importlib import import_module, util
import numpy as np

PYAUDIO_SPEC = util.find_spec("pyaudio")
if PYAUDIO_SPEC is not None:  # pragma: no cover - optional dependency for playback
    pyaudio = import_module("pyaudio")
else:  # pragma: no cover - optional dependency for playback
    pyaudio = None


NOTE_OFFSETS = {
    "C": -9,
    "C#": -8,
    "Db": -8,
    "D": -7,
    "D#": -6,
    "Eb": -6,
    "E": -5,
    "F": -4,
    "F#": -3,
    "Gb": -3,
    "G": -2,
    "G#": -1,
    "Ab": -1,
    "A": 0,
    "A#": 1,
    "Bb": 1,
    "B": 2,
}


@dataclass
class ADSR:
    attack: float = 0.01
    decay: float = 0.1
    sustain_level: float = 0.8
    release: float = 0.2

    def envelope(self, length: int, sample_rate: int) -> np.ndarray:
        """Create an ADSR envelope for a signal of a given length."""
        attack_samples = int(self.attack * sample_rate)
        decay_samples = int(self.decay * sample_rate)
        release_samples = int(self.release * sample_rate)

        sustain_samples = max(length - attack_samples - decay_samples - release_samples, 0)

        attack_env = np.linspace(0, 1, attack_samples, endpoint=False)
        decay_env = np.linspace(1, self.sustain_level, decay_samples, endpoint=False)
        sustain_env = np.full(sustain_samples, self.sustain_level)
        release_env = np.linspace(self.sustain_level, 0, release_samples, endpoint=False)

        envelope = np.concatenate((attack_env, decay_env, sustain_env, release_env))
        if envelope.size < length:
            # Pad to full length in case of rounding differences
            padding = np.full(length - envelope.size, 0.0)
            envelope = np.concatenate((envelope, padding))
        else:
            envelope = envelope[:length]
        return envelope


def note_to_frequency(note: str) -> float:
    """Convert note name (e.g., 'A4' or 'C#5') to frequency in Hz."""
    note = note.strip()
    if note.upper() == "R":
        return 0.0

    pitch = note[:-1]
    octave = int(note[-1])

    if pitch:
        pitch = pitch[0].upper() + pitch[1:]

    if pitch not in NOTE_OFFSETS:
        raise ValueError(f"Unknown note pitch: {pitch}")

    semitone_offset = NOTE_OFFSETS[pitch] + 12 * (octave - 4)
    return 440.0 * (2 ** (semitone_offset / 12))


def generate_waveform(wave_type: str, frequency: float, duration: float, sample_rate: int) -> np.ndarray:
    """Generate a waveform of the requested type."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    if frequency == 0:
        return np.zeros_like(t)

    angular = 2 * np.pi * frequency * t
    if wave_type == "sine":
        return np.sin(angular)
    if wave_type == "square":
        return np.sign(np.sin(angular))
    if wave_type == "sawtooth":
        return 2.0 * (frequency * t - np.floor(0.5 + frequency * t))

    raise ValueError(f"Unsupported wave type: {wave_type}")


def mix_waves(waves: Sequence[np.ndarray]) -> np.ndarray:
    """Mix multiple wave arrays, normalizing to prevent clipping."""
    if not waves:
        return np.array([], dtype=np.float32)

    max_length = max(len(w) for w in waves)
    aligned = [np.pad(w, (0, max_length - len(w))) for w in waves]
    mix = np.sum(aligned, axis=0)

    peak = np.max(np.abs(mix))
    if peak > 0:
        mix = mix / peak * 0.8  # keep some headroom
    return mix.astype(np.float32)


def apply_adsr_envelope(wave: np.ndarray, adsr: ADSR, sample_rate: int) -> np.ndarray:
    envelope = adsr.envelope(len(wave), sample_rate)
    return wave * envelope


def play_wave(wave: np.ndarray, sample_rate: int) -> None:
    """Play raw wave data using PyAudio."""
    if pyaudio is None:
        raise RuntimeError(
            "PyAudio is required for playback. Install with `pip install pyaudio`."
        )

    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paFloat32,
        channels=1,
        rate=sample_rate,
        output=True,
    )

    try:
        stream.write(wave.tobytes())
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()


def synthesize_tone(
    note: str,
    duration: float,
    oscillators: Iterable[Tuple[str, float]],
    adsr: ADSR,
    sample_rate: int,
) -> np.ndarray:
    frequency = note_to_frequency(note)
    waves = [amplitude * generate_waveform(wave_type, frequency, duration, sample_rate) for wave_type, amplitude in oscillators]
    mixed = mix_waves(waves)
    return apply_adsr_envelope(mixed, adsr, sample_rate)


def play_melody(
    melody: Sequence[Tuple[str, float]],
    oscillators: Iterable[Tuple[str, float]] = (("sine", 1.0),),
    adsr: ADSR = ADSR(),
    sample_rate: int = 44100,
) -> None:
    """Play a sequence of (note, duration) pairs."""
    buffer: List[np.ndarray] = []
    for note, duration in melody:
        tone = synthesize_tone(note, duration, oscillators, adsr, sample_rate)
        buffer.append(tone)
    song = np.concatenate(buffer)
    play_wave(song, sample_rate)


if __name__ == "__main__":
    DEMO_MELODY = [
        ("C4", 0.4),
        ("E4", 0.4),
        ("G4", 0.4),
        ("C5", 0.6),
        ("R", 0.2),
        ("E4", 0.4),
        ("G4", 0.4),
        ("B4", 0.4),
        ("D5", 0.6),
    ]

    DEFAULT_OSCILLATORS = (
        ("sine", 0.7),
        ("square", 0.15),
        ("sawtooth", 0.15),
    )

    print("Playing demo melody... (press Ctrl+C to stop)")
    play_melody(DEMO_MELODY, DEFAULT_OSCILLATORS)
