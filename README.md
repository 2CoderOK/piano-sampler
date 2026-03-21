# 🎹 piano-sampler

A lightweight, terminal-based piano sampler written in Python. It maps MIDI inputs to high-quality audio samples of a real Steinway & Sons Model B Grand Piano. 

[<img src="https://raw.githubusercontent.com/2coderok/piano-sampler/main/assets/sampler_preview.png" alt="piano-sampler preview" width="500"/>](https://www.youtube.com/watch?v=sa6QNgTfyXc)

*(Click the image to watch a video on how this sampler was created)*

## ✨ Features
* **Real-time MIDI Input:** Automatically detects and opens all available MIDI devices by default, or lets you specify exactly which ports to use (by name or index).
* **Embedded Audio Samples:** Loads directly from a packaged zip archive in-memory—no messy folder extraction needed.
* **Velocity Sensitive:** Responds to how hard you play the keys (can be toggled off).
* **Sustain Pedal Support:** Fully supports MIDI CC 64 for natural sustain pedal behavior.
* **Customizable Polyphony:** Adjust the maximum number of simultaneous voices to save CPU or handle complex chords.

## 🛠 Installation

You can install `piano-sampler` using `pip`, `uv` or build it directly from the source.

**Option 1: Install via PyPI (pip)**
pip install piano-sampler

**Option 2: Install via uv**
If you use [uv](https://github.com/astral-sh/uv) for fast Python package management:
uv tool install piano-sampler

**Option 3: Install from source (GitHub)**
git clone https://github.com/2CoderOK/piano-sampler.git
cd piano-sampler
pip install .

## 🚀 Usage

If you installed the package via `pip` or `uv`, simply run the command from your terminal:

piano-sampler

### ⚠️ Note for `uv` Global Users
If you installed via `uv tool install`, the application runs in an isolated environment. If the script fails to locate the audio files automatically, you will need to point it to the `piano_samples.zip` file located within the `uv` tool directory:

1. Locate your uv tool path (run `uv tool dir`) and find the install piano_samples.zip file (usually `/path/to/uv/tool/dir/Lib/site-packages/piano_sampler`).
2. Run the sampler by passing the path to the zip file:
piano-sampler --samples-path /path/to/the/piano_samples.zip

If you are running it directly from the cloned repository without installing:
python -m piano_sampler.main

### Command Line Arguments
You can customize the sampler's behavior using the following flags:

* `--list-ports`: Display a list of all available MIDI input devices (with their 0-based index numbers) and exit.
* `-p`, `--port [PORT ...]`: Specify one or more MIDI ports to open. You can use exact port names, 0-based index numbers, or a mix of both. If omitted, all available inputs are used.
* `--polyphony <int>`: Set the maximum number of simultaneous notes (Default: 32).
* `--ignore-velocity`: Play all notes at maximum volume, regardless of how hard you press the key.
* `--sustain`: Extend the default release time of notes when let go.
* `--samples-path <path>`: Specify a custom path to your `piano_samples.zip` file (Defaults to the packaged resource or `./piano_samples.zip`).

### 🎛 Keyboard Mode

You can use your computer keyboard as a simple piano controller instead of a MIDI device by passing the `--keyboard` (or `-k`) flag. This avoids opening MIDI ports — a small Pygame window will open to capture key events, and the sampler will play on key press and release on key release.

Usage example:

piano-sampler --keyboard

Key → Note mapping (layout):

    W     E             T     Y     U           O     P
A      S      D      F     G     H     J     K     L     ;     '
C4 Db4 D4 Eb4 E4    F4 F#4 G4 Ab4 A4 Bb4 B4 C5 Db5 D5 Eb5 E5  F5

Press `ESC` or close the window to exit keyboard mode.

**Examples:**

List available MIDI devices:
piano-sampler --list-ports

Open specific MIDI ports by 0-based index number or literal name:
piano-sampler -p "Arturia KeyStep 32"
piano-sampler -p 2

Open *multiple* MIDI ports simultaneously (mixing indices and names):
piano-sampler -p 0 2 "Arturia KeyStep 32"

Run with high polyphony and max volume (ignoring velocity):
piano-sampler --polyphony 64 --ignore-velocity

## License
Code: licensed under MIT (see LICENSE).
Audio: The audio samples in this package were taken from Electronic Music Studios, University of Iowa: 
https://theremin.music.uiowa.edu/MISpiano.html
Please consider supporting their work.

If you found this project helpful or fun to use, you can support my work here:

[<img alt="Buy me a coffee" height="50px" src="https://github.com/2CoderOK/jp-trainer/blob/main/yellow-button.png" />](https://www.buymeacoffee.com/coderok)

---


## 🚨 WARNING: INCOMING SHAMELESS PLUG 🚨
*Please avert your eyes if you are allergic to indie devs promoting their own stuff on their free MIT repos! 🫣*

**🎹 Meet this project's beefy C++ sibling: JazzPianoLab!**

[<img width="500px" alt="JazzPianoLabr" src="https://jazzpianolab.app/static/assets/img/illustrations/jpl_image_5.jpg" />](https://jazzpianolab.app/s/4p7ZtR)

I loved working on this Python sampler, but my curiosity got the better of me.
I really wanted to build my own highly controllable audio tool from the ground up, just to see what I could do.
Fast forward a bit and I accidentally spent way too much time creating a massive, supercharged platform called [JazzPianoLab](https://jazzpianolab.app/s/4p7ZtR)! 

It's written in C++ using the JUCE 8 audio framework and is packed with features I nerded out on:
* 🎹 **VST3 Virtual Instrument Support**
* 🎼 **Advanced Chord Profile System**
* ⚡ **Real-Time Chord Identification**
* 🔴 **Built-in MIDI Recorder**
* ...and much more!

Don't worry, this MIT Python project isn't going anywhere!
But if you’re looking for a next-level jazz piano training platform, check out [JazzPianoLab](https://jazzpianolab.app/s/4p7ZtR) for the latest updates and downloads.
Let’s make jazz piano learning smarter and more fun together!
