import pygame


def play_music(music_file):
    clock = pygame.time.Clock()
    try:
        pygame.mixer.music.load(music_file)
        print('Music file %s loaded!' % music_file)
    except pygame.error:
        print('File %s not found! (%s)' % (music_file, pygame.get_error()))
        return
    pygame.mixer.music.play()
    # while pygame.mixer.music.get_busy():
    #     # check if playback has finished
    #     clock.tick(30)


def check_if_playing():
    if pygame.mixer.get_init():
        return pygame.mixer.music.get_busy()


def pause_music():
    if pygame.mixer.get_init():
        pygame.mixer.music.pause()


def unpause_music():
    if pygame.mixer.get_init():
        pygame.mixer.music.unpause()


def stop_music():
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()


def prepare_and_play(file):
    freq = 44100  # audio CD quality
    bitsize = -16  # unsigned 16 bit
    channels = 2  # 1 is mono, 2 is stereo
    buffer = 1024  # number of samples
    pygame.mixer.init(freq, bitsize, channels, buffer)

    # optional volume 0 to 1.0
    pygame.mixer.music.set_volume(0.8)

    try:
        # Podaje nazwę pliku z dysku do odtworzenia
        # play_music('./data/result.mid')
        # play_music('././data/theRockingAntDrums.mid')
        play_music(file)
    except KeyboardInterrupt:
        # if user hits Ctrl/C then exit
        # (works only in console mode)
        pygame.mixer.music.fadeout(1000)
        pygame.mixer.music.stop()
        raise SystemExit


if __name__ == '__main__':
    prepare_and_play('../data/theRockingAntDrums.mid')
    # prepare_and_play('../data/theRockingAnt.mid')
    # prepare_and_play('../data/theDreamingAnt.mid')
    # prepare_and_play('../data/FishPolka.mid')
