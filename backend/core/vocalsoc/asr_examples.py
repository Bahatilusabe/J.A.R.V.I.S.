"""ASR helper examples: preprocessing and CTC postprocessing templates.

Drop-in helpers for `OfflineSpeechCache.preload_model(...)` to run common
CTC-style ASR models exported for OpenVINO. These are example templates and
should be adapted to your particular model's expected input layout,
normalization, and token mapping.
"""

from __future__ import annotations

from typing import Dict, Optional

def example_preprocess_wav_bytes(audio_bytes: bytes, sample_rate: int = 16000, n_mels: int = 80, input_name: Optional[str] = None):
    """Convert WAV bytes -> model input mapping expected by OpenVINO compiled model.

    Returns a dict: {input_name: numpy.ndarray} where the ndarray dtype is float32
    and shape matches what the model expects (batch dimension included).

    This example uses librosa to compute a log-mel spectrogram and normalizes
    it per-feature. Adjust n_fft/hop_length/win_length and axis reordering to
    fit your model.
    """
    try:
        import io
        import numpy as np
        import librosa  # pip install librosa soundfile
    except Exception as e:
        raise RuntimeError("example_preprocess requires librosa + numpy: %s" % e)

    buf = io.BytesIO(audio_bytes)
    wav, sr = librosa.load(buf, sr=sample_rate, mono=True)

    # compute mel spectrogram
    mel = librosa.feature.melspectrogram(y=wav, sr=sample_rate, n_mels=n_mels, power=1.0)
    log_mel = np.log1p(mel).astype(np.float32)

    # normalize per-channel
    mean = log_mel.mean(axis=1, keepdims=True)
    std = log_mel.std(axis=1, keepdims=True) + 1e-9
    log_mel = (log_mel - mean) / std

    # Common model layouts: (1, n_mels, frames) or (1, 1, n_mels, frames)
    arr = np.expand_dims(log_mel, axis=0)  # (1, n_mels, frames)
    # If your model needs (1, 1, frames, n_mels) transpose accordingly:
    # arr = arr[:, :, :, :].transpose(0, 2, 1)

    # Return mapping; caller should pass correct input_name for compiled model
    return {input_name or "input": arr}


def ctc_greedy_decoder(model_outputs, index2label, blank_index: int = 0) -> str:
    """Simple greedy CTC decoding from model outputs.

    model_outputs can be either a numpy array of shape (1, T, C) or a dict of
    outputs -> arrays (in which case the first array is used).
    """
    import numpy as np

    if isinstance(model_outputs, dict):
        arr = next(iter(model_outputs.values()))
    else:
        arr = model_outputs

    if arr.ndim == 3 and arr.shape[0] == 1:
        arr = arr[0]

    ids = np.argmax(arr, axis=-1).tolist()

    prev = None
    tokens = []
    for idx in ids:
        if idx == prev:
            prev = idx
            continue
        if idx != blank_index:
            tokens.append(index2label[idx])
        prev = idx

    text = "".join(tokens)
    return text


# Example token map for lowercase english + space; adjust to your model's vocabulary
INDEX2LABEL = [
    "<blank>", " ",
    "a","b","c","d","e","f","g","h","i","j","k","l","m",
    "n","o","p","q","r","s","t","u","v","w","x","y","z","'",
]


def wrapped_preprocess(audio_bytes: bytes):
    # default returns mapping with key 'input'; adapt input name when wiring
    return example_preprocess_wav_bytes(audio_bytes, input_name="input")


def wrapped_postprocess(outputs) -> str:
    return ctc_greedy_decoder(outputs, INDEX2LABEL, blank_index=0)


__all__ = [
    "example_preprocess_wav_bytes",
    "ctc_greedy_decoder",
    "INDEX2LABEL",
    "wrapped_preprocess",
    "wrapped_postprocess",
]
