import pyglet
from pyglet import shapes
from pyglet.window import key
from circle_music_common import *
from circle_music import run_music, stop_music, music_running, is_new_note, s, NOTE_LENGTH, USE_ARC_LENGTH, ARC_LENGTH_PER_NOTE, ARC_LENGTH_PER_NOTE_CURVE, calc_arc_length_duration
import math
from dataclasses import dataclass, field
from typing import Callable, List
from scamp_extensions.utilities import remap
import numpy as np


ORIGIN = WINDOW_DIM[0] / 2, WINDOW_DIM[1] / 2

@dataclass
class Path:
    positions: List[tuple[float, float]] = field(default_factory=list)
    timestamps: List[float] = field(default_factory=list)


# Pyglet setup
window = pyglet.window.Window(*WINDOW_DIM)
pyglet.gl.glClearColor(*[c / 255.0 for c in BACKGROUND_COLOR], 1)


main_path = Path()
main_path.positions.append(circle_spectrum_graphics.position_at(0, offset=ORIGIN))
main_path.timestamps.append(0)
played_positions = []


def update(dt):
    if not music_running():
        return
    t = get_time()

    x, y = circle_spectrum_graphics.position_at(t, offset=ORIGIN)

    main_path.positions.append((x, y))
    main_path.timestamps.append(t)

    if PATH_DECAY_TIME is not None:
        while main_path.timestamps and t - main_path.timestamps[0] > PATH_DECAY_TIME:
            main_path.timestamps.pop(0)
            main_path.positions.pop(0)



drawables = []


def draw_circles(t, batch):
    max_amplitude = np.max(circle_spectrum_graphics.spectrum[:, 1])
    positions_and_radii = circle_spectrum_graphics.circles_at(t, offset=ORIGIN)
    zero_phase_proximities = circle_spectrum_graphics.zero_phase_proximities(t)
    for (position, radius, _), zero_phase_proximity in zip(positions_and_radii, zero_phase_proximities):
        if DRAW_CIRCLE_PULSES:
            fill_opacity = int(zero_phase_proximity * remap(radius, 30, 200, 0, max_amplitude))
            drawables.append(pyglet.shapes.Circle(*position, radius, color=(255, 255, 0) + (fill_opacity,), batch=batch))
        drawables.append(pyglet.shapes.Circle(*position, CIRCLE_CENTER_DOT_WIDTH, color=CIRCLE_CENTER_COLOR, batch=batch))
        drawables.append(pyglet.shapes.Arc(*position, radius, color=CIRCLE_COLOR, thickness=CIRCLE_WIDTH,  batch=batch))
    

play_head_rad_mul = 1

    
def draw_play_head(t, batch):
    global play_head_rad_mul
    
    if is_new_note():
        if SHOW_PLAYED_POSITIONS:
            played_positions.append((*main_path.positions[-1], t))
        if SHOW_ONSETS:
            play_head_rad_mul = ONSET_ENLARGEMENT_MUL

    dot_radius = PATH_DOT_WIDTH * play_head_rad_mul

    drawables.append(shapes.Circle(*main_path.positions[-1], dot_radius, color=PATH_COLOR, batch=batch))


def draw_path(t, batch):
    if len(main_path.positions) > 1:
        for i in range(1, len(main_path.positions)):
            alpha = 255 if (PATH_DECAY_TIME is None or PATH_DECAY_TIME == 0) else int(255 * (1 - (t - main_path.timestamps[i]) / PATH_DECAY_TIME))
            color = PATH_COLOR + (alpha,)
            drawables.append(shapes.Line(main_path.positions[i-1][0], main_path.positions[i-1][1],
                                         main_path.positions[i][0], main_path.positions[i][1],
                                         width=PATH_WIDTH, color=color, batch=batch))


def draw_played_positions(t, batch):
    global played_positions
    played_positions = [pp for pp in played_positions if abs(t - pp[2]) < PLAYED_POSITION_FADE_TIME]
        
    for *position, play_time in reversed(played_positions):
        dot = shapes.Circle(*position, PLAYED_POSITION_DOT_WIDTH, color=PATH_COLOR, batch=batch)
        fade_progress = abs(t - play_time) / PLAYED_POSITION_FADE_TIME
        dot.opacity = int((1 - fade_progress) * 255)
        drawables.append(dot)



def draw_dashed_line(x1, y1, x2, y2, batch, dash_length=10, gap_length=5, color=(255, 255, 255)):
    """
    Draws a dashed line between two points.
    :param x1, y1: Starting point of the line.
    :param x2, y2: Ending point of the line.
    :param dash_length: Length of each dash.
    :param gap_length: Length of the gap between dashes.
    :param color: Color of the dashes.
    :param batch: Batch to draw the lines in. If None, creates a new batch.
    """
    dx = x2 - x1
    dy = y2 - y1
    distance = ((dx ** 2) + (dy ** 2)) ** 0.5
    dash_gap_total = dash_length + gap_length

    num_dashes = int(distance // dash_gap_total)
    for i in range(num_dashes):
        start_fraction = (i * dash_gap_total) / distance
        end_fraction = ((i * dash_gap_total) + dash_length) / distance

        start_x = x1 + (dx * start_fraction)
        start_y = y1 + (dy * start_fraction)
        end_x = x1 + (dx * end_fraction)
        end_y = y1 + (dy * end_fraction)

        drawables.append(shapes.Line(start_x, start_y, end_x, end_y, width=1, color=color, batch=batch))
        

if SAVE_FRAMES:
    frame = 0
    frame_time = 0
    
    # replace the get time function with one based on frames
    get_time = lambda: frame_time
    if not USE_ARC_LENGTH:
        is_new_note = lambda: frame_time % NOTE_LENGTH < (frame_time - 1 / FRAME_RATE) % NOTE_LENGTH
    else:
        next_new_note = 0
        def is_new_note():
            global next_new_note
            new_note = False
            while frame_time >= next_new_note:
                next_new_note += calc_arc_length_duration(next_new_note, ARC_LENGTH_PER_NOTE)
                new_note = True
            return new_note
    
    def increment_frame():
        global frame, frame_time, ARC_LENGTH_PER_NOTE_CURVE, ARC_LENGTH_PER_NOTE
        frame += 1
        frame_time += 1 / FRAME_RATE
        if ARC_LENGTH_PER_NOTE_CURVE:
            ARC_LENGTH_PER_NOTE = ARC_LENGTH_PER_NOTE_CURVE.value_at(frame_time)
        
    for _ in range(24000):
        increment_frame()

    
@window.event
def on_draw():
    global play_head_rad_mul
    drawables.clear()
    window.clear()
    if music_running():
        main_batch = pyglet.graphics.Batch()
        t = get_time()
        if DRAW_CIRCLES:
            draw_circles(t, main_batch)
        if SHOW_DASHED_DISTANCE:
            draw_dashed_line(WINDOW_DIM[0] / 2, WINDOW_DIM[1] / 2, *circle_spectrum_graphics.position_at(t, offset=ORIGIN), main_batch)
        if SHOW_PLAYED_POSITIONS:
            draw_played_positions(t, main_batch)
        draw_path(t, main_batch)
        draw_play_head(t, main_batch)
        main_batch.draw()
        play_head_rad_mul = ENLARGEMENT_DECAY_CONSTANT + (1 - ENLARGEMENT_DECAY_CONSTANT) * play_head_rad_mul

    if SAVE_FRAMES:
        if frame > 25000:
            pyglet.image.get_buffer_manager().get_color_buffer().save(f'frames/{frame:06}.png')
        increment_frame()

@window.event
def on_key_press(symbol, modifiers):
    if symbol == key.ESCAPE:
        window.close()


def start(dt):
    restart_time()
    run_music()


pyglet.clock.schedule_interval(update, 1/60.0)  # Update at 60Hz
pyglet.clock.schedule_once(start, 1)
pyglet.app.run()
stop_music()
exit()