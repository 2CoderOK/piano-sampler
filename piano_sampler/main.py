import argparse
import io
import logging
import sys
import tempfile
import time
import zipfile
from contextlib import ExitStack
from importlib import resources
from pathlib import Path
from collections.abc import Callable

import mido
import pygame
from pygame import mixer

LOG = logging.getLogger(__name__)
__version__ = "0.1.2"

# Computer keyboard → MIDI note number mapping
# Layout mirrors a piano keyboard: white keys on home row, black keys on top row
KEY_NOTE_MAP: dict[int, int] = {
    pygame.K_a: 60,  # C4
    pygame.K_w: 61,  # Db4
    pygame.K_s: 62,  # D4
    pygame.K_e: 63,  # Eb4
    pygame.K_d: 64,  # E4
    pygame.K_f: 65,  # F4
    pygame.K_t: 66,  # F#4
    pygame.K_g: 67,  # G4
    pygame.K_y: 68,  # Ab4
    pygame.K_h: 69,  # A4
    pygame.K_u: 70,  # Bb4
    pygame.K_j: 71,  # B4
    pygame.K_k: 72,  # C5
    pygame.K_o: 73,  # Db5
    pygame.K_l: 74,  # D5
    pygame.K_p: 75,  # Eb5
    pygame.K_SEMICOLON: 76,  # E5
    pygame.K_QUOTE: 77,  # F5
}


class Sampler:
    """Plays sample files mapped to MIDI note numbers."""

    def __init__(
        self,
        mix: mixer,
        polyphony: int = 32,
        ignore_velocity: bool = False,
        sustain: bool = False,
        samples_path: Path = None,
    ) -> None:
        mix.set_num_channels(polyphony)

        self.ignore_velocity = ignore_velocity
        self.sustain = sustain

        if samples_path is not None:
            self.samples_path = Path(samples_path)
        else:
            try:
                archive_path = resources.files("piano_sampler")
                if archive_path.is_dir():
                    with resources.as_file(archive_path) as p:
                        self.samples_path = Path(p)
            except Exception:
                LOG.error(
                    "Failed to locate audio resources; please specify --samples-path with path to piano_samples.zip"
                )
                exit(1)

        self.id_to_file: dict[int, str] = {}
        self.sounds: dict[int, mixer.Sound] = {}
        self.pedal_pressed: bool = False
        self.note_off_q: list[int] = []

        self._build_mappings()
        self._load_sounds(mix)

    def _build_mappings(self) -> None:
        notes = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
        octave = 1
        notes_id = 0
        for i in range(24, 96):
            name = notes[notes_id]
            self.id_to_file[i] = f"Piano.ff.{name}{octave}.flac"
            notes_id += 1
            if notes_id >= len(notes):
                notes_id = 0
            if i in [23, 35, 47, 59, 71, 83]:
                octave += 1

    def _load_sounds(self, mix: mixer) -> None:
        zf = None
        try:
            if self.samples_path.is_file():
                with resources.as_file(self.samples_path) as p:
                    zf = zipfile.ZipFile(p)
            else:
                # packaged as a binary resource inside wheel
                with resources.open_binary("piano_sampler", "piano_samples.zip") as f:
                    zf = zipfile.ZipFile(io.BytesIO(f.read()))
        except Exception:
            zf = None

        for note_id, filename in self.id_to_file.items():
            # Prefer archive if present and contains the file
            if zf and filename in zf.namelist():
                data = zf.read(filename)
                bio = io.BytesIO(data)
                bio.seek(0)
                try:
                    # Try in-memory load first
                    self.sounds[note_id] = mix.Sound(file=bio)
                    continue
                except Exception:
                    # Fallback to a temp file if pygame can't load from BytesIO
                    tf = tempfile.NamedTemporaryFile(suffix=".flac", delete=False)
                    tf.write(data)
                    tf.flush()
                    tf.close()
                    try:
                        self.sounds[note_id] = mix.Sound(tf.name)
                        continue
                    except Exception:
                        LOG.exception(f"Failed to load sample from archive for {filename}")
            # Fallback: look in filesystem path (existing behavior)
            path = self.samples_path / filename
            if not path.exists():
                LOG.warning(f"Missing sample for note {note_id}: {path}")
                continue
            try:
                self.sounds[note_id] = mix.Sound(str(path))
            except Exception:
                LOG.exception(f"Failed to load sound {path} for note {note_id}")

    def play(self, note_id: int, vel: int) -> None:
        sound = self.sounds.get(note_id)
        if sound is None:
            LOG.debug(f"No sound mapped for note {note_id}")
            return
        LOG.debug(f"play({note_id}, {vel})")
        sound.fadeout(150)
        if not self.ignore_velocity:
            sound.set_volume((vel / 127.0) if vel is not None else 1.0)
        sound.play()

    def stop(self, note_id: int) -> None:
        sound = self.sounds.get(note_id)
        if sound is None:
            LOG.debug(f"stop() called for unmapped note {note_id}")
            return
        LOG.debug(f"stop({note_id})")
        sound.fadeout(600 if self.sustain else 300)


def run_keyboard_mode(sampler: Sampler) -> None:
    """Event loop that maps computer keyboard keys to sampler notes."""
    pygame.display.init()
    pygame.display.set_mode((520, 80))
    pygame.display.set_caption("Piano Sampler - Keyboard Mode  (ESC / close to quit)")
    pygame.key.set_repeat(0)  # disable OS key-repeat so held keys don't re-trigger
    pressed_keys: set[int] = set()
    LOG.info(
        "Keyboard mode active — "
        "A/S/D/F/G/H/J/K/L/;/' = white keys  "
        "W/E/T/Y/U/O/P = black keys  "
        "ESC or close window to quit"
    )
    try:
        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        return
                    if ev.key in KEY_NOTE_MAP and ev.key not in pressed_keys:
                        pressed_keys.add(ev.key)
                        sampler.play(KEY_NOTE_MAP[ev.key], 100)
                elif ev.type == pygame.KEYUP:
                    if ev.key in KEY_NOTE_MAP and ev.key in pressed_keys:
                        pressed_keys.discard(ev.key)
                        sampler.stop(KEY_NOTE_MAP[ev.key])
            time.sleep(0.01)
    except KeyboardInterrupt:
        LOG.info("Interrupted by user, exiting")


def make_note_handler(sampler: Sampler) -> Callable[[mido.Message], None]:
    def _handler(msg: mido.Message) -> None:
        try:
            if msg.type in ("note_on", "note_off"):
                note_id = int(msg.note) if msg.note is not None else -1
                if msg.type == "note_on":
                    LOG.debug(f"note_on: {note_id}")
                    sampler.play(note_id, getattr(msg, "velocity", 127))
                    if note_id in sampler.note_off_q:
                        sampler.note_off_q.remove(note_id)
                else:
                    LOG.debug(f"note_off: {note_id}")
                    if sampler.pedal_pressed:
                        sampler.note_off_q.append(note_id)
                    else:
                        sampler.stop(note_id)
            elif msg.type == "control_change" and getattr(msg, "control", None) == 64:
                sampler.pedal_pressed = bool(getattr(msg, "value", 0))
                LOG.debug(f"pedal {'pressed' if sampler.pedal_pressed else 'released'}")
                if not sampler.pedal_pressed:
                    for nid in sampler.note_off_q:
                        sampler.stop(nid)
                    sampler.note_off_q.clear()
        except Exception:
            LOG.exception(f"Error handling MIDI message: {msg}")

    return _handler


def main(argv: list[str] | None = None) -> None:
    LOG.info(f"Starting piano-sampler version {__version__}")
    parser = argparse.ArgumentParser(description="Simple MIDI sampler")
    parser.add_argument("--list-ports", action="store_true")
    parser.add_argument(
        "--keyboard",
        "-k",
        action="store_true",
        help="Use computer keyboard instead of MIDI input",
    )
    parser.add_argument("--ignore-velocity", action="store_true")
    parser.add_argument("--sustain", action="store_true")
    parser.add_argument("--polyphony", type=int, default=32)
    parser.add_argument("--samples-path", type=Path, default=Path("./piano_samples.zip"))
    parser.add_argument(
        "--port",
        "-p",
        nargs="+",
        help="MIDI port numbers (0-based) or names; if omitted, all available inputs are used",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.list_ports:
        ports = mido.get_input_names()
        if not ports:
            LOG.info("No MIDI input devices found.")
        else:
            LOG.info("Available MIDI input devices:")
            for port in ports:
                LOG.info(f"- {port}")
        return

    try:
        mixer.init()
    except Exception:
        LOG.exception("Failed to initialize mixer")
        sys.exit(1)

    sampler = Sampler(mixer, args.polyphony, args.ignore_velocity, args.sustain, args.samples_path)

    if args.keyboard:
        run_keyboard_mode(sampler)
        return

    midi_ports = mido.get_input_names()
    if not midi_ports:
        LOG.error("No MIDI devices found. Please connect a controller and try again!")
        sys.exit(0)

    # Determine which ports to open: user-specified or all available
    if args.port:
        requested = list(args.port)
        selected = []
        missing = []
        for req in requested:
            # accept 0-based index numbers or literal names
            try:
                idx = int(req)
                if 0 <= idx < len(midi_ports):
                    selected.append(midi_ports[idx])
                else:
                    missing.append(req)
            except ValueError:
                if req in midi_ports:
                    selected.append(req)
                else:
                    missing.append(req)
        if missing:
            LOG.warning("Requested MIDI ports not found: %s", missing)
        if not selected:
            LOG.error("No requested MIDI ports available, exiting")
            sys.exit(1)
    else:
        selected = midi_ports

    handler = make_note_handler(sampler)

    try:
        with ExitStack() as stack:
            inputs = [
                stack.enter_context(mido.open_input(name, callback=handler)) for name in selected
            ]
            LOG.info(f"Opened {len(inputs)} MIDI input(s): {selected}")
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        LOG.info("Interrupted by user, exiting")


if __name__ == "__main__":
    main()
