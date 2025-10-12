import time, uuid, threading
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import numpy as np
import requests

from ..deps import require_xauth
from ..audio import download_files, preprocess_to_16k_mono, compute_speaker_embedding, save_model_npz
from ..tts_preview import synth_preview
from ..storage import upload_to_s3, public_url
from ..core.config import settings
from ..deps import require_xauth

# 💡 수정: 백엔드 AiService.java의 호출 경로에 맞게 prefix를 "/train"으로 변경
router = APIRouter(tags=["train"])

# In-memory job store
JOBS: dict[str, dict] = {}  # job_id -> info

# Java AiService 호환 스펙
class TrainStartReq(BaseModel):
    voiceFileId: str = Field(..., description="Voice file UUID from Spring")
    voiceFileUrl: str = Field(..., description="S3 URL of voice file")
    userId: str = Field(..., description="User UUID")
    walletAddress: str = Field(..., description="User wallet address")
    originalFilename: Optional[str] = Field(None, description="Original filename")
    duration: Optional[float] = Field(None, description="Duration in seconds")

class TrainStartResp(BaseModel):
    jobId: str  # Java에서 jobId로 받음
    status: str = "TRAINING"

DATA_ROOT = Path("/data")

def _train_worker(job_id: str, voice_file_id: str, voice_file_url: str, user_id: str, wallet_address: str, original_filename: Optional[str]):
    """
    1) 다운로드 -> 2) 전처리 -> 3) 임베딩 추출(=학습) -> 4) 모델 저장 -> 5) 프리뷰 생성 -> 6) S3 업로드 -> 7) 콜백
    """
    import os
    import time
    import requests

    cb_url = os.getenv("SPRING_CALLBACK_URL")  # Spring Boot 콜백 URL
    secret = os.getenv("X_AUTH_SHARED_SECRET", "CHANGE_ME")
    timeout = int(os.getenv("CALLBACK_TIMEOUT", "10"))

    
    cb_url = settings.SPRING_CALLBACK_URL
    secret = settings.X_AUTH_SHARED_SECRET
    timeout = settings.CALLBACK_TIMEOUT
    b_models = settings.S3_BUCKET_MODELS
    b_preview = settings.S3_BUCKET_PREVIEW

    # 디렉터리 셋업
    model_dir = DATA_ROOT / "models" / voice_file_id
    raw_dir   = DATA_ROOT / "raw" / voice_file_id
    prep_dir  = DATA_ROOT / "prep" / voice_file_id
    out_dir   = DATA_ROOT / "out" / voice_file_id
    for d in (model_dir, raw_dir, prep_dir, out_dir):
        d.mkdir(parents=True, exist_ok=True)

    training_start_time = time.time()

    try:
        # 1) 다운로드
        JOBS[job_id].update(status="TRAINING", progress=5, message="downloading audio file")
        wav_paths = download_files([voice_file_url], raw_dir)
        
        if not wav_paths:
            raise RuntimeError("Failed to download audio file")

        # 2) 전처리(16k mono + trim)
        JOBS[job_id].update(progress=25, message="preprocessing audio")
        prep_paths = preprocess_to_16k_mono(wav_paths, prep_dir)

        # 3) 임베딩 추출(=경량 학습)
        JOBS[job_id].update(progress=55, message="extracting voice features")
        emb = compute_speaker_embedding(prep_paths)  # np.array (256-d)

        # 4) 모델 저장 (npz)
        JOBS[job_id].update(progress=65, message="saving voice model")
        model_npz = save_model_npz(emb, model_dir)

        # 5) 프리뷰 생성(xtts_v2)
        JOBS[job_id].update(progress=80, message="generating preview")
        preview_text = os.getenv("PREVIEW_TEXT_KO", "안녕하세요, 오디온입니다. 이 목소리는 데모로 생성된 프리뷰입니다.")
        lang = os.getenv("PREVIEW_LANG", "ko")
        ref_wav = prep_paths[0]  # 가장 첫 샘플 하나로 참조
        preview_wav = out_dir / "preview.wav"
        synth_preview(ref_wav, preview_wav, preview_text, lang=lang)

        # 6) S3 업로드
        JOBS[job_id].update(progress=92, message="uploading to cloud")
        # 모델 파일 (private)
        model_key = f"models/{voice_file_id}/model.npz"
        model_s3_uri = upload_to_s3(model_npz, b_models, model_key, public=False)
        
        # 프리뷰 wav (public)
        preview_key = f"preview/{voice_file_id}/preview.wav"
        preview_s3_uri = upload_to_s3(preview_wav, b_preview, preview_key, public=True)
        preview_public = public_url(b_preview, preview_key)

        # 학습 소요 시간 계산
        training_duration = int(time.time() - training_start_time)

        # 7) 완료
        JOBS[job_id].update(
            status="DONE", 
            progress=100, 
            message="training completed successfully",
            voiceFileId=voice_file_id,
            modelPath=model_s3_uri, 
            previewUrl=preview_public,
            trainingDurationSeconds=training_duration
        )

        # Spring Boot 콜백 (Java ModelTrainCompleteCallbackRequest 스펙에 맞춤)
        if cb_url:
            payload = {
                # 💡 수정: 백엔드가 VoiceFile ID를 modelId 필드로 받으므로, voice_file_id를 전달
                "modelId": voice_file_id,
                "status": "DONE",
                "modelPath": model_s3_uri,
                "previewUrl": preview_public,
                "trainingDurationSeconds": training_duration,
                "jobId": job_id,
                "aiServerVersion": "1.0.0"
            }
            try:
                response = requests.post(
                    cb_url, 
                    json=payload, 
                    headers={"X-AUTH": secret}, 
                    timeout=timeout
                )
                if response.status_code == 200:
                    print(f"✅ Callback successful for job {job_id}")
                else:
                    print(f"⚠️  Callback failed with status {response.status_code} for job {job_id}")
            except Exception as e:
                print(f"❌ Callback error for job {job_id}: {str(e)}")

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Training failed for job {job_id}: {error_msg}")
        
        JOBS[job_id].update(
            status="ERROR", 
            progress=0,
            message=f"Training failed: {error_msg}",
            voiceFileId=voice_file_id
        )
        
        # 실패 콜백
        if cb_url:
            payload = {
                # 💡 수정: 실패 시에도 voice_file_id를 modelId로 전달
                "modelId": voice_file_id,
                "status": "ERROR",
                "errorMessage": error_msg,
                "jobId": job_id
            }
            try:
                requests.post(
                    cb_url, 
                    json=payload, 
                    headers={"X-AUTH": secret}, 
                    timeout=timeout
                )
            except Exception:
                pass  # 콜백 실패해도 조용히 넘어감

@router.post("/train", response_model=TrainStartResp)
async def start_training(req: TrainStartReq, _: bool = Depends(require_xauth)):
    """Java AiService와 호환되는 학습 시작 엔드포인트"""
    
    if not req.voiceFileUrl or not req.voiceFileUrl.strip():
        raise HTTPException(status_code=400, detail="voiceFileUrl is required")
    
    if not req.voiceFileId or not req.voiceFileId.strip():
        raise HTTPException(status_code=400, detail="voiceFileId is required")

    # 고유한 Job ID 생성
    job_id = "job_" + uuid.uuid4().hex[:12]
    
    # Job 상태 초기화
    JOBS[job_id] = {
        "jobId": job_id,
        "status": "TRAINING", 
        "progress": 0, 
        "message": "initializing training",
        "voiceFileId": req.voiceFileId,
        "userId": req.userId,
        "walletAddress": req.walletAddress,
        "originalFilename": req.originalFilename,
        "startedAt": time.time()
    }
    
    # 백그라운드에서 학습 시작
    thread = threading.Thread(
        target=_train_worker, 
        args=(job_id, req.voiceFileId, req.voiceFileUrl, req.userId, req.walletAddress, req.originalFilename),
        daemon=True
    )
    thread.start()
    
    print(f"🚀 Started training job {job_id} for voice file {req.voiceFileId}")
    
    return TrainStartResp(jobId=job_id, status="TRAINING")

# 학습 상태 조회
@router.get("/status/{job_id}")
async def get_training_status(job_id: str, _: bool = Depends(require_xauth)):
    """학습 상태 조회"""
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return {
        "jobId": job_id,
        "status": job.get("status", "UNKNOWN"),
        "progress": job.get("progress", 0),
        "message": job.get("message", ""),
        "voiceFileId": job.get("voiceFileId"),
        "modelPath": job.get("modelPath"),
        "previewUrl": job.get("previewUrl"),
        "startedAt": job.get("startedAt"),
        "trainingDurationSeconds": job.get("trainingDurationSeconds")
    }

# 모든 Job 상태 조회 (관리용)
@router.get("/jobs")
async def list_all_jobs(_: bool = Depends(require_xauth)):
    """모든 학습 Job 목록 조회 (관리용)"""
    return {
        "totalJobs": len(JOBS),
        "jobs": [
            {
                "jobId": job_id,
                "status": job.get("status"),
                "progress": job.get("progress", 0),
                "voiceFileId": job.get("voiceFileId"),
                "startedAt": job.get("startedAt")
            }
            for job_id, job in JOBS.items()
        ]
    }

# Job 삭제 (관리용)
@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, _: bool = Depends(require_xauth)):
    """완료된 Job 삭제 (관리용)"""
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    job = JOBS[job_id]
    if job.get("status") == "TRAINING":
        raise HTTPException(status_code=400, detail="Cannot delete running job")
    
    del JOBS[job_id]
    return {"message": f"Job {job_id} deleted successfully"}