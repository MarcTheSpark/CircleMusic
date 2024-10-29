Server.default.options.numOutputBusChannels = 18

(
ScampUtils.instrumentFromSynthDef(
	SynthDef(\pad, {
		arg freq = 440, volume = 0.5, gate = 1, brightness = 0.5, pan = 0, out = 0;
		var snd;
		snd = Saw.ar(freq * { LFNoise2.kr(20 ! 16)  * 0.2}.midiratio * [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2]);
		snd = DelayC.ar(snd, 0.01, { Rand(0, 0.01) } ! snd.size);
		snd = Splay.ar(snd);
		snd = LPF.ar(snd, brightness.linexp(0, 1, 100, 1000));
		snd = BPeakEQ.ar(snd, freq * 8, 0.1, 8);
		snd = snd * EnvGate(0, gate, 0.1);
		snd = snd * volume;
		Out.ar(out * 2, Pan2.ar(snd, pan));
	})
);
)

(
ScampUtils.instrumentFromSynthDef(
	SynthDef(\pad, {
		arg freq = 440, volume = 0.5, gate = 1, brightness = 0.5, pan = 0, out = 0;
		var snd;
		snd = Saw.ar(freq * { LFNoise2.kr(20 ! 16)  * 0.2}.midiratio * [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2]);
		snd = DelayC.ar(snd, 0.01, { Rand(0, 0.01) } ! snd.size);
		snd = Splay.ar(snd);
		snd = LPF.ar(snd, brightness.linexp(0, 1, 100, 1000));
		snd = BPeakEQ.ar(snd, freq * 8, 0.1, 8);
		snd = snd * EnvGate(0, gate, 0.1);
		snd = snd * volume;
		Out.ar(0, Pan2.ar(snd, Rand(-1, 1)));
	})
);
)

s.record(numChannels:18);
s.stopRecording;

x = Synth(\pad, [\freq, 440])
x.set(\brightness, 0.9)

MarcUtilities.setOutputLimiter(0.5, 0.25)
Server.default.options.outDevices; // output devices

NetAddr.localAddr