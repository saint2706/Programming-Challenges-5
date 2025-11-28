# Simple Music Synthesizer

This Python script demonstrates a minimal music synthesizer that can generate sine, square, and sawtooth waveforms, shape them with an ADSR envelope, and play them through PyAudio. A small demo melody is included when running the module directly.

## Features

- Waveform generation (sine, square, sawtooth) at configurable frequencies.
- ADSR envelope control (attack, decay, sustain level, release) for shaping volume.
- Multiple oscillators can be mixed to create richer tones.
- Play back arbitrary melodies by providing note/duration pairs.

## Usage

1. Install dependencies (NumPy and PyAudio):
   ```bash
   pip install -r ../requirements.txt
   ```
2. Run the demo melody:
   ```bash
   python synthesizer.py
   ```
3. Import and play your own melody:

   ```python
   from synthesizer import play_melody, ADSR

   custom_adsr = ADSR(attack=0.02, decay=0.1, sustain_level=0.7, release=0.3)
   melody = [("C4", 0.5), ("E4", 0.5), ("G4", 1.0)]
   play_melody(melody, oscillators=(("sine", 0.8), ("sawtooth", 0.2)), adsr=custom_adsr)
   ```

> **Note:** If PyAudio is not installed or audio output is unavailable, `play_wave` will raise a `RuntimeError`. Waveform generation functions can still be used without PyAudio.
