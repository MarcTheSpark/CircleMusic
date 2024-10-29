from scamp import Envelope

transition_width = 0.8

CYCLE = 12.8


levels = [0,
          10,
          64,
          64,
          10,
          0]


durations = [CYCLE * 9,
             CYCLE * 3,
             CYCLE,
             CYCLE * 2,
             CYCLE * 4]

curve_shapes = [0, 4,
                0,
                -4, 0]

transitions_envelope = Envelope(levels, durations, curve_shapes)


if __name__ == '__main__':
    transitions_envelope.show_plot()