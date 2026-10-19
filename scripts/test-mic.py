import sounddevice as sd, numpy as np, time

def cb(indata, frames, t, status):
    rms = float(np.sqrt(np.mean(indata**2)))
    if rms > 0.01:
        print(f'rms={rms:.4f}', flush=True)

with sd.InputStream(samplerate=44100, blocksize=1024, channels=1, dtype='float32', callback=cb):
    print('Snap now — watching for 5 seconds...')
    time.sleep(5)
