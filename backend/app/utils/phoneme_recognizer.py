"""
Zero-shot speech → IPA via a multilingual phoneme recogniser.

Phase 1 uses an off-the-shelf wav2vec2 CTC model trained to emit IPA phones for
any language (`settings.PHONEME_MODEL`). It has never
heard Bavarian, so expect rough output; fine-tuning on Nativo's own recordings
+ `WordForm.ipa_pronunciation` is the planned next step.

torch/transformers are heavy and optional: install with `uv sync --extra asr`.
Without them `recognize` raises `RecognizerUnavailableError` and the IPA-only path
still works. Decoding uses the `ffmpeg` binary, so any browser recording format
(webm/ogg/mp3/wav/m4a) is accepted.
"""

from __future__ import annotations

import subprocess
import tempfile
from functools import lru_cache

SAMPLE_RATE = 16_000
# Longer clips are truncated: segmentation cost grows with the phone count.
MAX_SECONDS = 15


class RecognizerUnavailableError(RuntimeError):
    """ASR dependencies or the ffmpeg binary are missing."""


@lru_cache(maxsize=1)
def _load():
    try:
        import torch  # noqa: F401
        from transformers import (
            Wav2Vec2FeatureExtractor,
            Wav2Vec2ForCTC,
            Wav2Vec2PhonemeCTCTokenizer,
        )
    except ImportError as exc:
        raise RecognizerUnavailableError(
            "Speech recognition is not installed on this server (uv sync --extra asr)"
        ) from exc

    from app.config import settings

    name = settings.PHONEME_MODEL
    model = Wav2Vec2ForCTC.from_pretrained(name).eval()
    extractor = Wav2Vec2FeatureExtractor.from_pretrained(name)
    # do_phonemize=False: we only decode ids → phones, so espeak isn't needed.
    tokenizer = Wav2Vec2PhonemeCTCTokenizer.from_pretrained(name, do_phonemize=False)
    return model, extractor, tokenizer


def _decode_audio(audio: bytes):
    import numpy as np

    # A temp file, not stdin: MP4/m4a (iPhone, Safari recordings) keeps its
    # index at the end of the file, so ffmpeg must be able to seek.
    try:
        with tempfile.NamedTemporaryFile() as src:
            src.write(audio)
            src.flush()
            proc = subprocess.run(
                [
                    "ffmpeg",
                    "-nostdin",
                    "-loglevel",
                    "error",
                    "-i",
                    src.name,
                    "-t",
                    str(MAX_SECONDS),
                    "-ac",
                    "1",
                    "-ar",
                    str(SAMPLE_RATE),
                    "-f",
                    "f32le",
                    "pipe:1",
                ],
                capture_output=True,
                check=True,
            )
    except FileNotFoundError as exc:
        raise RecognizerUnavailableError("ffmpeg is not installed on this server") from exc
    except subprocess.CalledProcessError as exc:
        raise ValueError("Could not decode the audio file") from exc
    wave = np.frombuffer(proc.stdout, dtype=np.float32)
    if wave.size == 0:
        raise ValueError("The audio file is empty")
    return wave


def recognize(audio: bytes) -> str:
    """Return space-separated IPA phones for an audio clip (no word boundaries)."""
    model, extractor, tokenizer = _load()
    import torch

    wave = _decode_audio(audio)
    inputs = extractor(wave, sampling_rate=SAMPLE_RATE, return_tensors="pt")
    with torch.inference_mode():
        logits = model(inputs.input_values).logits
    ids = torch.argmax(logits, dim=-1)[0]
    return tokenizer.decode(ids).strip()
