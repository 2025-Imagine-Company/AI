#!/usr/bin/env python3
"""
Integration test script for AudIon AI server
Run this after installing requirements.txt to verify everything works
"""

def test_imports():
    """Test all critical imports"""
    try:
        # Core FastAPI
        from app.main import app
        print("✅ Main app imports successfully")
        
        # Router integration
        from app.routers.train import router
        print("✅ Train router imports successfully")
        
        # Dependencies
        from app.deps import require_xauth
        print("✅ Authentication deps import successfully")
        
        # Audio processing
        from app.audio import download_files, preprocess_to_16k_mono, compute_speaker_embedding, save_model_npz
        print("✅ Audio processing functions import successfully")
        
        # Storage
        from app.storage import upload_to_s3, public_url
        print("✅ S3 storage functions import successfully")
        
        # TTS
        from app.tts_preview import synth_preview
        print("✅ TTS preview function imports successfully")
        
        # Config
        from app.core.config import settings
        print("✅ Settings import successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_app_startup():
    """Test FastAPI app can be created"""
    try:
        from app.main import create_app
        app = create_app()
        print("✅ FastAPI app creates successfully")
        print(f"✅ App title: {app.title}")
        print(f"✅ App version: {app.version}")
        return True
    except Exception as e:
        print(f"❌ App startup error: {e}")
        return False

def main():
    print("🧪 Testing AudIon AI Server Integration...")
    print()
    
    success = True
    
    print("1. Testing imports...")
    success &= test_imports()
    print()
    
    print("2. Testing app startup...")
    success &= test_app_startup()
    print()
    
    if success:
        print("🎉 All integration tests passed!")
        print("💡 Ready to run: uvicorn app.main:app --host 0.0.0.0 --port 8081")
    else:
        print("❌ Some tests failed. Check the errors above.")
        print("💡 Make sure to install: pip install -r requirements.txt")

if __name__ == "__main__":
    main()