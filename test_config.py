#!/usr/bin/env python3
import os
from dotenv import load_dotenv, find_dotenv
from app.core.config import Settings

print("=== Environment Variables ===")
print(f"SPRING_CALLBACK_URL from os.environ: {os.environ.get('SPRING_CALLBACK_URL', 'NOT FOUND')}")
print(f"X_AUTH_SHARED_SECRET from os.environ: {os.environ.get('X_AUTH_SHARED_SECRET', 'NOT FOUND')}")

print("\n=== Loading .env manually ===")
load_dotenv(find_dotenv(), override=True)
print(f"SPRING_CALLBACK_URL after load_dotenv: {os.environ.get('SPRING_CALLBACK_URL', 'NOT FOUND')}")

print("\n=== Settings object values ===")
settings = Settings()
print(f"settings.SPRING_CALLBACK_URL: {settings.SPRING_CALLBACK_URL}")
print(f"settings.X_AUTH_SHARED_SECRET: {settings.X_AUTH_SHARED_SECRET}")