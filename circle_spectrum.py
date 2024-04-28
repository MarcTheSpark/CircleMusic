from expenvelope import Envelope
import numpy as np
import math
from functools import lru_cache

class CircleSpectrum:
    
    def __init__(self, *freq_amp_phase_tuples, cutoff_index=None, normalize=False):
        """
        Cutoff index determines how much of the spectrum to express. Can be a float, in which case only a fraction
        of the amplitude of the final circle is included.
        """
        self.spectrum = np.array(freq_amp_phase_tuples)
        self.cutoff_index = len(self.spectrum) if cutoff_index is None else cutoff_index
        if normalize:
            self.normalize()
        
    def sort_by_frequency(self, reverse=False):
        self.spectrum = self.spectrum[np.argsort(self.spectrum[:, 0])[::-1]] \
                        if reverse else  self.spectrum[np.argsort(self.spectrum[:, 0])]
    
    def sort_by_amplitude(self, reverse=True):
        self.spectrum = self.spectrum[np.argsort(self.spectrum[:, 1])[::-1]] \
                        if reverse else  self.spectrum[np.argsort(self.spectrum[:, 1])]
        
    def circles_at(self, t, offset=(0, 0)):
        """
        Returns a list of (position, radius, phase) tuples.
        """
        active_spectrum = self.active_spectrum_at(t)
        components = self.components_at(t)
        offset = offset[0] + offset[1]*1j
        phases = active_spectrum[:, 2] + 2 * math.pi * t * active_spectrum[:, 0]
        return [
            (CircleSpectrum._complex_to_tup(np.sum(components[:i]) + offset), active_spectrum[i][1], phases[i])
            for i in range(len(components))
        ]
    
    def circle_info_at(self, t, which_circle, offset=(0, 0)):
        """
        Returns (position, radius, phase) tuple
        """
        active_spectrum = self.active_spectrum_at(t)
        if which_circle >= len(active_spectrum):
            # trying to access a circle that's inactive
            return None, 0, self.spectrum[which_circle][2] + 2 * math.pi * t * self.spectrum[which_circle][0]
        components = self.components_at(t)
        offset = offset[0] + offset[1]*1j
        position = CircleSpectrum._complex_to_tup(np.sum(components[:which_circle]) + offset)
        amplitude = active_spectrum[which_circle][1]
        phase = active_spectrum[which_circle][2] + 2 * math.pi * t * active_spectrum[which_circle][0]
        return position, amplitude, phase

        
    @lru_cache(maxsize=10)
    def active_spectrum_at(self, t):
        cutoff_index = self.cutoff_index.value_at(t)
        truncated_spectrum = np.array(self.spectrum[: math.ceil(cutoff_index)])
        if cutoff_index != int(cutoff_index):
            truncated_spectrum[-1][1] *= cutoff_index - int(cutoff_index)
        return truncated_spectrum
    
    @lru_cache(maxsize=10)
    def components_at(self, t):
        active_spectrum = self.active_spectrum_at(t)
        return active_spectrum[:, 1] * np.exp(1j * (2 * np.pi * active_spectrum[:, 0] * t + active_spectrum[:, 2]))
    
    def position_at(self, t, offset=(0, 0)):
        offset = offset[0] + offset[1]*1j
        return CircleSpectrum._complex_to_tup(np.sum(self.components_at(t)) + offset)
    
    def speed_at(self, t, dt=0.001):
        position_ahead = self.position_at(t + dt/2)
        position_behind = self.position_at(t - dt/2)
        return math.hypot(position_ahead[0] - position_behind[0], position_ahead[1] - position_behind[1]) / dt
    
    @staticmethod
    def _complex_to_tup(complex_value):
        return float(complex_value.real), float(complex_value.imag)
        
    @property
    def cutoff_index(self):
        return self._cutoff_index
        
    @cutoff_index.setter
    def cutoff_index(self, value):
        if not isinstance(value, Envelope):
            value = Envelope(value)
        self._cutoff_index = value
        
    def set_cutoff_percent(self, percent):
        self.cutoff_index = len(self.spectrum) * percent
        
    def normalize(self, total_amplitude=1):
        self.spectrum[:, 1] *= total_amplitude / np.sum(self.spectrum[:, 1])
        
    def normalized(self, total_amplitude=1):
        normalized = CircleSpectrum(*self.spectrum, cutoff_index=self.cutoff_index)
        normalized.normalize(total_amplitude)
        return normalized
    
    def zero_phase_proximities(self, t):
        return CircleSpectrum.zero_phase_proximity(self.spectrum[:, 0], self.spectrum[:, 2], t)
    
    @staticmethod
    def zero_phase_proximity(freq, phase, t):
        return (np.cos(freq * t * 2 * math.pi + phase) + 1) / 2
    
    def max_speed(self, t=None):
        active_spectrum = self.active_spectrum_at(t) if t is not None else self.spectrum
        # tangential velocity = r * 2pi * f (f must be made positive), and we sum them all up,
        # assuming that they are all moving in the same direction
        return np.sum(active_spectrum[:, 1] * 2 * np.pi * np.abs(active_spectrum[:, 0]))
        
    
if __name__ == '__main__':
    cs = CircleSpectrum(
        (0.0330585657, 0.5118651025640375, 4.003892984091995),
        (0.0594847553, 0.26514079548427716, 5.126214392942125),
        (0.1101511383, 0.15481882287084747, 3.62161623022389),
        (0.2485596714, 0.06817527908083781, 0.7531753373593039),
    )
    cs.sort_by_frequency()
    print(cs.spectrum)

