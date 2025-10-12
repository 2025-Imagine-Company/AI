import os
import subprocess
import torch
from pathlib import Path
from typing import List
import numpy as np
import soundfile as sf
import librosa
import requests
from speechbrain.pretrained import EncoderClassifier

_encoder = None

def get_encoder():
    """SpeechBrain 음성 인코더 (speaker embedding 추출용)"""
    global _encoder
    if _encoder is None:
        _encoder = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir="tmp_models/spkrec-ecapa-voxceleb"
        )
    return _encoder

def download_files(urls: List[str], output_dir: Path) -> List[Path]:
    """URL에서 파일들을 다운로드"""
    downloaded = []
    
    for url in urls:
        try:
            filename = url.split('/')[-1].split('?')[0] or "audio.wav"
            output_path = output_dir / filename
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            downloaded.append(output_path)
            print(f"✅ Downloaded: {filename}")
            
        except Exception as e:
            print(f"❌ Failed to download {url}: {str(e)}")
    
    return downloaded

def preprocess_to_16k_mono(input_paths: List[Path], output_dir: Path) -> List[Path]:
    """
    오디오 파일들을 16kHz mono로 변환하고 무음 제거
    """
    processed = []
    
    for input_path in input_paths:
        try:
            # 오디오 로드 (자동으로 16kHz로 리샘플링)
            audio, sr = librosa.load(input_path, sr=16000, mono=True)
            
            # 무음 제거 (음성 활동 감지)
            audio_trimmed, _ = librosa.effects.trim(audio, top_db=20)
            
            # 너무 짧으면 스킵 (최소 1초)
            if len(audio_trimmed) < 16000:
                print(f"⚠️  Audio too short after trimming: {input_path.name}")
                continue
            
            # 출력 경로
            output_path = output_dir / f"{input_path.stem}_16k.wav"
            
            # 저장
            sf.write(output_path, audio_trimmed, 16000)
            processed.append(output_path)
            
            print(f"✅ Preprocessed: {input_path.name} -> {output_path.name}")
            
        except Exception as e:
            print(f"❌ Failed to preprocess {input_path}: {str(e)}")
    
    return processed

def compute_speaker_embedding(audio_paths: List[Path]) -> np.ndarray:
    """
    여러 오디오 파일들로부터 화자 임베딩 추출 (평균)
    """
    encoder = get_encoder()
    embeddings = []
    
    for audio_path in audio_paths:
        try:
            # SpeechBrain으로 임베딩 추출
            signal, fs = sf.read(audio_path)
            
            # 모노로 변환 (스테레오인 경우)
            if len(signal.shape) > 1:
                signal = signal.mean(axis=1)
            
            # 임베딩 추출 (batch_size=1)
            embedding = encoder.encode_batch(
                torch.tensor(signal).unsqueeze(0)
            )
            
            # numpy로 변환
            emb_np = embedding.squeeze().cpu().numpy()
            embeddings.append(emb_np)
            
            print(f"✅ Extracted embedding from: {audio_path.name}")
            
        except Exception as e:
            print(f"⚠️  Failed to extract embedding from {audio_path}: {str(e)}")
    
    if not embeddings:
        raise RuntimeError("No embeddings could be extracted from audio files")
    
    # 여러 임베딩의 평균 (더 안정적인 화자 표현)
    mean_embedding = np.mean(embeddings, axis=0)
    
    # L2 정규화
    mean_embedding = mean_embedding / np.linalg.norm(mean_embedding)
    
    return mean_embedding

def save_model_npz(embedding: np.ndarray, output_dir: Path) -> Path:
    """
    화자 임베딩을 .npz 형식으로 저장
    """
    output_path = output_dir / "model.npz"
    
    # 메타데이터와 함께 저장
    np.savez_compressed(
        output_path,
        embedding=embedding,
        embedding_size=len(embedding),
        model_version="1.0.0",
        encoder="speechbrain/spkrec-ecapa-voxceleb"
    )
    
    print(f"✅ Saved model: {output_path}")
    return output_path

# PyTorch import (SpeechBrain이 필요로 함)
try:
    import torch
except ImportError:
    print("⚠️  PyTorch not found. Installing required for SpeechBrain...")
    subprocess.check_call(["pip", "install", "torch", "torchaudio"])