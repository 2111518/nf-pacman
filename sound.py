import pygame
import os
from typing import Dict, Optional

class SoundController:
    """Manages loading and playing sound effects and music."""

    def __init__(self, music_dir: str = "Music") -> None:
        """
        Initializes the SoundController and loads all sounds.

        Args:
            music_dir: The directory where sound files are located.
        """
        if not pygame.mixer.get_init():
            pygame.mixer.init() # Ensure mixer is initialized

        self.music_dir: str = music_dir
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.load_sounds()
        self.current_background_music_name: Optional[str] = None

    def load_sounds(self) -> None:
        """Loads all .wav sound files from the music directory."""
        if not os.path.isdir(self.music_dir):
            print(f"Warning: Music directory '{self.music_dir}' not found.")
            return

        for filename in os.listdir(self.music_dir):
            if filename.endswith(".wav"):
                name: str = os.path.splitext(filename)[0]
                filepath: str = os.path.join(self.music_dir, filename)
                try:
                    self.sounds[name] = pygame.mixer.Sound(filepath)
                except pygame.error as e:
                    print(f"")
        #print(f"Loaded {len(self.sounds)} sounds from '{self.music_dir}'.")


    def play_sound(self, name: str, loops: int = 0, maxtime: int = 0, fade_ms: int = 0) -> Optional[pygame.mixer.Channel]:
        """
        Plays a loaded sound.

        Args:
            name: The name of the sound to play (without .wav extension).
            loops: Number of times to repeat the sound. 0 means play once. -1 means loop indefinitely.
            maxtime: Maximum time to play the sound in milliseconds.
            fade_ms: Fade-in time in milliseconds.

        Returns:
            The Channel object if the sound was played, None otherwise.
        """
        if name in self.sounds:
            sound: pygame.mixer.Sound = self.sounds[name]
            try:
                channel: Optional[pygame.mixer.Channel] = sound.play(loops=loops, maxtime=maxtime, fade_ms=fade_ms)
                return channel
            except pygame.error as e:
                print(f"Error playing sound '{name}': {e}")
                return None
        else:
            print(f"Warning: Sound '{name}' not found.")
            return None

    def play_background_music(self, name: str, loops: int = -1, start_time: float = 0.0, fade_ms: int = 0) -> None:
        """
        Plays a sound as background music. Stops any currently playing music.

        Args:
            name: The name of the sound file to play (without .wav extension).
            loops: Number of times to repeat the music. -1 means loop indefinitely.
            start_time: The position in seconds to start playing from.
            fade_ms: Fade-in time in milliseconds.
        """
        if name == self.current_background_music_name and pygame.mixer.music.get_busy():
            return

        if name in self.sounds:
            filepath: str = os.path.join(self.music_dir, name + ".wav")
            try:
                pygame.mixer.music.load(filepath)
                pygame.mixer.music.play(loops=loops, start=start_time, fade_ms=fade_ms)
                self.current_background_music_name = name
            except pygame.error as e:
                print(f"Error playing background music '{name}': {e}")
                self.current_background_music_name = None
        else:
            print(f"Warning: Background music '{name}' not found.")
            self.current_background_music_name = None

    def stop_music(self) -> None:
        """Stops the currently playing background music."""
        try:
            pygame.mixer.music.stop()
            self.current_background_music_name = None
        except pygame.error as e:
            print(f"Error stopping music: {e}")

    def fadeout_music(self, time: int) -> None:
        """
        Fades out the currently playing background music.

        Args:
            time: Time in milliseconds for the music to fade out.
        """
        try:
            pygame.mixer.music.fadeout(time)
            self.current_background_music_name = None
        except pygame.error as e:
            print(f"Error fading out music: {e}")

if __name__ == '__main__':
    # Example Usage (requires a Pygame display to be initialized for sound to work properly on some systems)
    pygame.init()
    screen = pygame.display.set_mode((200, 200)) # Dummy screen
    pygame.display.set_caption("Sound Test")

    # Create a dummy Music directory and a sound file for testing
    if not os.path.exists("Music"):
        os.makedirs("Music")

    # Create a simple sine wave .wav file for testing if no sounds are present
    # This is a very basic placeholder and might not work on all systems
    # or produce a pleasant sound.
    sample_rate = 44100
    freq = 440  # A4 note
    duration_ms = 1000
    bits = 16
    channels = 1 # mono

    # Check if any .wav files exist in Music directory
    has_wav_files = any(f.endswith('.wav') for f in os.listdir("Music"))

    if not has_wav_files:
        print("No .wav files found in Music directory. Attempting to create a dummy 'test_sound.wav'.")
        try:
            import math
            import wave

            n_samples = int(sample_rate * (duration_ms / 1000.0))
            max_amplitude = 2**(bits -1) -1

            wav_file = wave.open(os.path.join("Music", "test_sound.wav"), "w")
            wav_file.setparams((channels, bits // 8, sample_rate, n_samples, "NONE", "not compressed"))

            for i in range(n_samples):
                angle = 2 * math.pi * freq * i / sample_rate
                sample_value = int(max_amplitude * math.sin(angle))
                wav_file.writeframesraw(sample_value.to_bytes(bits // 8, byteorder='little', signed=True))
            wav_file.close()
            print("Dummy 'test_sound.wav' created.")
        except Exception as e:
            print(f"Could not create dummy 'test_sound.wav': {e}")
            print("Please add some .wav files to the 'Music' directory to test sounds.")


    sound_controller = SoundController()

    # Test playing a sound (replace 'test_sound' with an actual sound name if you have one)
    # For example, if you have 'munch_1.wav', use 'munch_1'
    test_sound_name = None
    if "test_sound" in sound_controller.sounds:
        test_sound_name = "test_sound"
    elif sound_controller.sounds: # Play the first available sound if test_sound is not there
        test_sound_name = list(sound_controller.sounds.keys())[0]


    if test_sound_name:
        print(f"Playing sound: {test_sound_name}")
        sound_controller.play_sound(test_sound_name)
        pygame.time.wait(1000) # Wait for the sound to play

        # Test background music (using the same sound)
        print(f"Playing background music: {test_sound_name}")
        sound_controller.play_background_music(test_sound_name)
        pygame.time.wait(3000) # Let it play for a bit
        sound_controller.stop_music()
        print("Stopped background music.")

        print(f"Playing background music with fadeout: {test_sound_name}")
        sound_controller.play_background_music(test_sound_name)
        pygame.time.wait(1000)
        sound_controller.fadeout_music(2000) # Fade out over 2 seconds
        pygame.time.wait(2000) # Wait for fadeout
        print("Finished music fadeout.")

    else:
        print("No sounds available to test in the Music directory.")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        pygame.display.flip()

    pygame.quit() 