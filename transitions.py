from scamp import Envelope

transition_width = 0.8

CYCLE = 21.6


levels = [0,
          0.5,
          1,
          1,
          1.5,
          2,
          2]


durations = [CYCLE/2,
             CYCLE/2,
             CYCLE * (1 - transition_width / 2),
             CYCLE * (transition_width / 2),
             CYCLE * (transition_width / 2),
             CYCLE * (1 - transition_width)]

curve_shapes = [2,
                -2,
                0,
                3,
                -3,
                0]

while levels[-1] < 8:
    levels.extend([levels[-1] + 0.5, levels[-1] + 1, levels[-1] + 1])
    durations.extend([CYCLE * (transition_width / 2), CYCLE * (transition_width / 2), CYCLE * (1 - transition_width)])
    curve_shapes.extend([3, -3, 0])
    
levels.extend([25, 40, 40, 10, 0])
durations.extend([CYCLE/2, CYCLE/2, CYCLE * 2, CYCLE, CYCLE * 7])
curve_shapes.extend([3, -3, 0, 3, 0])


transitions_envelope = Envelope(levels, durations, curve_shapes)

if __name__ == '__main__':
    transitions_envelope.show_plot()