from pydantic import BaseModel, Field
from typing import Optional

# Spring 서버의 AiService.requestTrain()이 보내는 요청 본문
class TrainRequest(BaseModel):
    voiceFileId: str
    voiceFileUrl: str
    userId: str
    walletAddress: str
    originalFilename: Optional[str] = None
    duration: Optional[float] = 0.0
    jobId: Optional[str] = None # 서버에서 생성하여 채워넣을 필드

# Spring 서버의 ModelTrainCompleteCallbackRequest DTO와 일치하는 콜백 모델
class TrainCallback(BaseModel):
    modelId: str
    status: str # "SUCCESS" 또는 "FAILED"
    modelPath: Optional[str] = Field(None, description="Path to the trained model file in S3")
    previewUrl: Optional[str] = Field(None, description="URL for the audio preview")
    errorMessage: Optional[str] = Field(None, description="Error message if training failed")
    jobId: Optional[str] = None
    trainingDurationSeconds: Optional[int] = None