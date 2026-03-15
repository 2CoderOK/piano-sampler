import pytest
from unittest.mock import MagicMock, patch
import mido

# Importing directly from your main package
from piano_sampler.main import Sampler, make_note_handler


@pytest.fixture
def mock_mixer():
    """Provides a mocked pygame mixer to avoid requiring actual audio hardware."""
    mixer = MagicMock()
    mixer.Sound = MagicMock()
    return mixer


@pytest.fixture
def sampler(mock_mixer):
    """Provides a Sampler instance with mocked sound loading."""
    # We patch _load_sounds so it doesn't try to read real zips/files during tests
    with patch("piano_sampler.main.Sampler._load_sounds"):
        s = Sampler(mix=mock_mixer, polyphony=32, ignore_velocity=False)
        # Inject a mock sound for testing play/stop logic on middle C (note 60)
        s.sounds[60] = MagicMock()
        return s


def test_build_mappings(sampler):
    """Test if MIDI note numbers map to the correct pitch and octave filenames."""
    # Note 24 should be C1
    assert sampler.id_to_file[24] == "Piano.ff.C1.flac"
    # Note 35 should be B1
    assert sampler.id_to_file[35] == "Piano.ff.B1.flac"
    # Note 36 should be C2
    assert sampler.id_to_file[36] == "Piano.ff.C2.flac"
    # Note 95 should be B6
    assert sampler.id_to_file[95] == "Piano.ff.B6.flac"


def test_play_note_applies_velocity(sampler):
    """Test that playing a note sets the correct volume and triggers play."""
    sampler.play(note_id=60, vel=64)
    sound_mock = sampler.sounds[60]

    sound_mock.fadeout.assert_called_with(150)
    # Volume should be velocity / 127
    sound_mock.set_volume.assert_called_with(64 / 127.0)
    sound_mock.play.assert_called_once()


def test_play_note_ignore_velocity(mock_mixer):
    """Test that velocity is ignored if the flag is set."""
    with patch("piano_sampler.main.Sampler._load_sounds"):
        s = Sampler(mix=mock_mixer, ignore_velocity=True)
        s.sounds[60] = MagicMock()

        s.play(note_id=60, vel=64)
        # set_volume shouldn't be called based on velocity if we ignore it
        s.sounds[60].set_volume.assert_not_called()


def test_note_handler_routes_messages(sampler):
    """Test that MIDI note_on and note_off messages route to play() and stop()."""
    handler = make_note_handler(sampler)

    # Test note_on
    msg_on = mido.Message("note_on", note=60, velocity=100)
    with patch.object(sampler, "play") as mock_play:
        handler(msg_on)
        mock_play.assert_called_once_with(60, 100)

    # Test note_off
    msg_off = mido.Message("note_off", note=60, velocity=0)
    with patch.object(sampler, "stop") as mock_stop:
        handler(msg_off)
        mock_stop.assert_called_once_with(60)


def test_sustain_pedal_logic(sampler):
    """Test that the sustain pedal queues note_offs and releases them when lifted."""
    handler = make_note_handler(sampler)

    # 1. Press sustain pedal (CC 64)
    msg_pedal_down = mido.Message("control_change", control=64, value=127)
    handler(msg_pedal_down)
    assert sampler.pedal_pressed is True

    # 2. Trigger note_off while pedal is pressed
    msg_off = mido.Message("note_off", note=60, velocity=0)
    with patch.object(sampler, "stop") as mock_stop:
        handler(msg_off)
        # Should NOT stop the sound yet
        mock_stop.assert_not_called()
        # Should be queued instead
        assert 60 in sampler.note_off_q

    # 3. Release sustain pedal
    msg_pedal_up = mido.Message("control_change", control=64, value=0)
    with patch.object(sampler, "stop") as mock_stop:
        handler(msg_pedal_up)
        assert sampler.pedal_pressed is False
        # NOW the queued note should stop
        mock_stop.assert_called_once_with(60)
        assert len(sampler.note_off_q) == 0
