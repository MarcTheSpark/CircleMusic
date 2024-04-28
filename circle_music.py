from scamp import *
from scamp_extensions.pitch import ScaleType, Scale
from scamp_extensions.utilities import remap, wrap_to_range
from circle_music_common import circle_spectrum_music, get_time
from fractions import Fraction
import random
import numpy as np
import math


rationalized_harmonic_minor = Scale(
    ScaleType(Fraction(9, 8), Fraction(6, 5), Fraction(4, 3), Fraction(45, 32), Fraction(3, 2), Fraction(8, 5), Fraction(9, 5), Fraction(15, 8), Fraction(2, 1)),
    57)


USE_ARC_LENGTH = False 
NOTE_LENGTH = 0.45  # if not using arc length
ARC_LENGTH_PER_NOTE = 0.06 # if using arc length
ARC_LENGTH_PER_NOTE_CURVE = Envelope([0.12, 0.06, 0.06, 0.12], [200, 100, 120], [-3, 0, 3]) 
SCALE = rationalized_harmonic_minor
AVOID_REPEATED_NOTES = True


def radius_to_pitch(r):
    return 60 + 42 * r



scale_type = ScaleType("9/8", "5/4", "4/3", "3/2", "5/3", "15/8", "2/1")

scale_sequence = [
    Scale(scale_type.rotate(k, in_place=False), 60)
    for k in (6, 2, 5, 1, 4, 0, 3)
] + [
    Scale(scale_type.rotate(k, in_place=False), 61)
    for k in (6, 2, 5, 1, 4)
]


if SCALE is None:
    def get_scale(position):
        angle = math.atan2(position[1], position[0])
        index = int((angle + math.pi) * 12 / math.tau)
        return scale_sequence[index]
else:
    def get_scale(position):
        return SCALE


if __name__ != '__main__':
    s = Session().run_as_server()
else:
    s = Session()
    get_time = lambda: s.time()


s.synchronization_policy = "no synchronization"
s.timing_policy = 0.5

piano = s.new_midi_part("", midi_output_device="midi through 0")

sc_pad = s.new_osc_part("pad", 57120)

piano.send_midi_cc(64, 1)

held_pitch_classes = set()


def _change_pedal():
    piano.send_midi_cc(64, 0.5)
    wait(0.1)
    held_pitch_classes.clear()
    piano.send_midi_cc(64, 1)


NEW_NOTE = False

def is_new_note():
    global NEW_NOTE
    out = NEW_NOTE
    NEW_NOTE = False 
    return out


# def play_sub_circles(inst, which_circles, pitches, pans=None):
#     if pans is None:
#         pans = np.linspace(-1, 1, len(which_circles))
#     if not len(which_circles) == len(pitches) == len(pans):
#         raise ValueError("Lengths of `which_circles`, `pitches`, and `pans` do not match")
#     t = get_time()
#     active_spectrum = circle_spectrum_music.active_spectrum_at(t)
#     circle_notes = []
#     max_amplitude = np.max(circle_spectrum_music.spectrum[:, 1])
#     for which_circle in which_circles:
#         position, radius, phase = circle_infos[which_circle]
#         amp = remap(radius, 0.1, 0.9, 0, max_amplitude) * 
# #         circle_notes.append(inst.start_note(
        

max_radius = np.max(circle_spectrum_music.spectrum[:, 1])
def amp_from_radius(radius): return remap(radius ** 0.5, 0, 0.7, 0, max_radius ** 0.5)


def play_sub_circle(inst, n, pitch, pan=0):
    position, radius, phase = circle_spectrum_music.circle_info_at(get_time(), n)
    freq = circle_spectrum_music.spectrum[n][0]
    
    output_chan = n if n < 8 else 8
    if freq == 0:
        amp = amp_from_radius(radius) if radius > 0 else 0
        note = inst.start_note(pitch, amp, f"param_brightness: {amp ** 0.5}, param_out: {output_chan}")
        while True:
            wait(0.5)
            radius = circle_spectrum_music.circle_info_at(get_time(), n)[1]
            amp = amp_from_radius(radius) if radius > 0 else 0
            note.change_volume(amp, 0.4)
    else:
        cycle_dur = 1 / abs(freq)

        initial_wait_radians = wrap_to_range(math.pi - phase, 0, 2 * math.pi) if freq > 0 else \
                               wrap_to_range(math.pi - phase , -2 * math.pi, 0)
        initial_wait = initial_wait_radians / (2 * math.pi * freq)
        
#         current_amp = amp_from_radius(radius) * circle_spectrum_music.zero_phase_proximity(freq, phase, get_time())
#         inst.play_note(pitch, [current_amp, 0], initial_wait, f"param_brightness: [{current_amp}, 0], param_pan: {pan}")
        wait(initial_wait)
        while True:
            _, radius, _ = circle_spectrum_music.circle_info_at(get_time() + cycle_dur / 2, n)
            if radius == 0:
                wait(cycle_dur)
            else:
                amp = amp_from_radius(radius)
                inst.play_note(pitch, [0, amp, 0], 1 / abs(freq), f"param_brightness: [0, {amp ** 0.5}, 0], param_out: {output_chan}")
        

def calc_arc_length_duration(t, arc_length_to_cover, tstep=0.001, max_t=50):
    start_t = t
    position = circle_spectrum_music.position_at(t)
    accumulated_arc_length = 0
    while accumulated_arc_length < arc_length_to_cover:
        t += tstep
        new_position = circle_spectrum_music.position_at(t)
        accumulated_arc_length += math.hypot(new_position[0] - position[0], new_position[1] - position[1])
        position = new_position
        if t - start_t > max_t:
            return math.inf
    return t - start_t


def main_melody_sonification():
    global NEW_NOTE, ARC_LENGTH_PER_NOTE      
    last_scale_degree = None 
    while True:
        t = get_time()
        if ARC_LENGTH_PER_NOTE_CURVE:
            ARC_LENGTH_PER_NOTE = ARC_LENGTH_PER_NOTE_CURVE.value_at(t)
        note_dur = calc_arc_length_duration(t, ARC_LENGTH_PER_NOTE) if USE_ARC_LENGTH else NOTE_LENGTH
        position = circle_spectrum_music.position_at(t)
        speed = circle_spectrum_music.speed_at(t)
        scale = get_scale(position)
        r = math.hypot(*position)
        scale_degree_float = scale.pitch_to_degree(radius_to_pitch(r))
        scale_degree = round(scale_degree_float)
        if scale_degree == last_scale_degree and AVOID_REPEATED_NOTES:
            scale_degree += 1 if scale_degree_float > scale_degree else -1
        held_pitch_classes.add(scale[scale_degree] % 12)
        if len(held_pitch_classes) > 6:
            s.fork(_change_pedal)
        NEW_NOTE = True
        piano.play_note(scale[scale_degree], remap(speed, 0.3, 0.8, 0, circle_spectrum_music.max_speed()) + random.uniform(0, 0.1), note_dur) 
        last_scale_degree = scale_degree



def main():
    for i, pitch in enumerate(rationalized_harmonic_minor[-9, -4, 2, 6, 8, 10, 12, 16, 17, 18, 19, 20, 21, 22, 23, 24]):
        if i >= len(circle_spectrum_music.spectrum):
            continue
        s.fork(play_sub_circle, (sc_pad, i, pitch, random.uniform(-1, 1)))
    main_melody_sonification()
    wait_forever()
    

music_clock = None


def run_music():
    global music_clock
    music_clock = s.fork(main)


def music_running():
    return music_clock is not None


def stop_music():
    global music_clock
    piano.send_midi_cc(64, 0)
    piano.end_all_notes()
    music_clock.kill()
    music_clock = None

if __name__ == '__main__':
#     s.start_transcribing()
#     run_music()
#     wait(20)
#     stop_music()
#     s.stop_transcribing().to_score().show()
    main()
    