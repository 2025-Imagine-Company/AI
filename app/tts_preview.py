import os
from pathlib import Path
from TTS.api import TTS
import torch
from TTS.tts.configs.xtts_config import XttsConfig
# Import the classes that need to be allowlisted
from TTS.tts.models.xtts import XttsAudioConfig
try:
    from TTS.tts.models.xtts import Xtts
    from TTS.tts.layers.xtts.gpt import GPT
    from TTS.tts.layers.xtts.hifigan_decoder import HifiDecoder
    from TTS.vocoder.models.hifigan import HifiganConfig
    xtts_classes = [Xtts, GPT, HifiDecoder, HifiganConfig]
except ImportError:
    xtts_classes = []

# Add ALL necessary classes to the list of safe globals for torch.load
torch.serialization.add_safe_globals([
    XttsConfig,
    XttsAudioConfig
] + xtts_classes)

# Set the environment variable to agree to the Coqui TTS license
os.environ["COQUI_TOS_AGREED"] = "1"

# 첫 로드가 무거우므로, 프로세스 단위로 1회만 로딩
_tts_singleton = None

def get_tts():
    global _tts_singleton
    if _tts_singleton is None:
        # GPU 사용 안 하려면 gpu=False
        _tts_singleton = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2",
                             progress_bar=False, gpu=False)
    return _tts_singleton

def synth_preview(ref_wav: Path, out_wav: Path, text: str, lang: str = "ko"):
    tts = get_tts()
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    # speaker_wav 하나만 넘겨 빠르게 합성 (임베딩 직접 주입은 API 내부 처리)
    tts.tts_to_file(text=text, speaker_wav=str(ref_wav), language=lang, file_path=str(out_wav))
    return out_wav