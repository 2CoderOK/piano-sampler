import sys
import time

import mido
from pygame import mixer

SAMPLER_POLYPHONY = 32


class Sampler:
    """
    A Sampler class that plays audio files on demand
    """

    def __init__(self, mix: mixer, ignore_velocity: bool, sustain: bool) -> None:
        """
        Load audio files and map them to midi notes ids
        """
        mix.set_num_channels(SAMPLER_POLYPHONY)

        self.ignore_velocity = ignore_velocity
        self.sustain = sustain
        self.id_to_note = {}
        self.id_to_file = {}
        notes = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
        octave = 1
        notes_id = 0
        for i in range(24, 96):
            self.id_to_note[i] = f"{notes[notes_id]}"
            self.id_to_file[i] = f"Piano.ff.{notes[notes_id]}{octave}.aiff"
            notes_id += 1
            if len(notes) == notes_id:
                notes_id = 0
            if i in [23, 35, 47, 59, 71, 83]:
                octave += 1
        self.sounds = {}
        for note_id, name in self.id_to_file.items():
            self.sounds[note_id] = mix.Sound("audio/" + name)

    def play(self, note_id: int, vel: int) -> None:
        """
        Play an audio file mapped to a given note_id (midi note id)
        using a velocity supplied in the midi message
        """
        print(f"play({note_id}, {vel})")
        self.sounds[note_id].stop()
        if not self.ignore_velocity:
            self.sounds[note_id].set_volume(float((vel / 127) * 1.0))
        self.sounds[note_id].play()

    def stop(self, note_id: int) -> None:
        """
        Stop playing an audio file mapped to a given note_id (midi note id)
        Fadeout sounds better (less cracking) and setting it to bigger values (over 200)
        helps playing without a sustain pedal
        """
        print(f"stop({note_id})")
        self.sounds[note_id].fadeout(600 if self.sustain else 300)


mixer.init()
sampler = None


def note_handler(note: mido.Message) -> None:
    """
    Handle midi note_on and note_off messages
    """
    if note.type in ["note_on", "note_off"]:
        note_id = int(note.note) if note.note is not None else -1
        if note.type == "note_on":
            print(f"note_on: {note_id}")
            sampler.play(note_id, note.velocity)
        elif note.type == "note_off":
            print(f"note_off: {note_id}")
            sampler.stop(note_id)


if __name__ == "__main__":
    try:
        IGNORE_VELOCITY = "--ignore_velocity" in sys.argv
        SUSTAIN = "--sustain" in sys.argv
        sampler = Sampler(mixer, IGNORE_VELOCITY, SUSTAIN)

        midi_ports = mido.get_input_names()
        portname = None
        if not midi_ports:
            print( "\nNo MIDI devices found. Please connect a controller and try again!" )
            exit( 0 )
        if len(midi_ports) == 1:
            portnum = 1
        else:
            # more than one MIDI device found
            print( "Found MIDI devices:" )
            for i, port in enumerate( midi_ports ):
                print( f"{i+1}. {port}." )
            while True:
                try:
                    portnum = input( "\nChoose a device by indicating its number as presented above: " )
                    portnum = int(portnum)
                    if (portnum < 1) or (portnum > len(midi_ports)):
                        raise ValueError
                    break
                except ValueError:
                    print(f"Please indicate a valid number in range [1-{len(midi_ports)}]")
        portname = midi_ports[portnum-1]

        with mido.open_input(portname, callback=note_handler) as port:
            print(f"Using {port}")
            while True:
                # A dummy loop to give some time for CPU to use for better stuff :)
                time.sleep(0.1)
    except KeyboardInterrupt:
        pass
