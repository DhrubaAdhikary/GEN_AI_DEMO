import os
import json
import asyncio
from pathlib import Path
from typing import Any

import boto3
import google.generativeai as genai
from config.loader import load_config, select_env, get_setting


# -----------------------------
# Load config & select ENV
# -----------------------------
print()
ENV = os.getenv("ENV")
_cfg_all = load_config(ENV)                 # resolves .../config/app_config.yaml via loader.py
_ENV_NAME, _ENV_CFG = select_env(ENV,_cfg_all)  # e.g., 'DEV', cfg dict under DEV

# -----------------------------
# Settings (with env-var overrides)
# -----------------------------
AWS_REGION = (
    os.getenv("AWS_REGION")
    or get_setting(_ENV_CFG, "aws.region", "us-east-1")
)

# Gemini settings
_GEMINI_CFG = get_setting(_ENV_CFG, "llms.gemini", {}) or {}
GEMINI_MODEL_ID = _GEMINI_CFG.get("model_id", "gemini-2.5-pro")
GEMINI_SECRET_NAME = _GEMINI_CFG.get("secret_name")              
GEMINI_SECRET_KEY  = _GEMINI_CFG.get("secret_key")              
GEMINI_ENV_TAG     = (_cfg_all.get("env", "DEV") or "DEV").lower()

_GEMINI_MODELS: dict[str, Any] = {}

def _safe_stream_text_piece(ev):
    """Safely extract text from streaming event"""
    try:
        return ev.text if hasattr(ev, 'text') else None
    except:
        return None

def _get_gemini_model(model_id: str | None = None):
    model_id = model_id or GEMINI_MODEL_ID
    if model_id not in _GEMINI_MODELS:
        _GEMINI_MODELS[model_id] = genai.GenerativeModel(model_id, generation_config={"temperature": 0})
    return _GEMINI_MODELS[model_id]


async def astream_gemini_synthesis(model_id:str,prompt:str,on_event=None):
    loop=asyncio.get_running_loop()
    model=_get_gemini_model(model_id)
    def _sync_iter(): return model.generate_content(prompt,stream=True)
    stream=await loop.run_in_executor(None,_sync_iter)
    for ev in stream:
        piece=_safe_stream_text_piece(ev)
        if piece:
            if on_event:
                try:on_event(piece)
                except:pass
            yield piece

# Allow explicit overrides if needed
GEMINI_SECRET_NAME = os.getenv("GEMINI_SECRET_NAME", GEMINI_SECRET_NAME)
GEMINI_SECRET_KEY  = os.getenv("GEMINI_SECRET_KEY", GEMINI_SECRET_KEY)

if not GEMINI_SECRET_NAME or not GEMINI_SECRET_KEY:
    raise RuntimeError(
        "Gemini secret_name/secret_key not found. "
        "Check DEV.llms.gemini.secret_name and secret_key in app_config.yaml."
    )


client = boto3.client(service_name="secretsmanager", region_name="us-east-1")
# # print(":::::: Config Env - ",env,"::::::")

gemini_secret_val = client.get_secret_value(SecretId=GEMINI_SECRET_NAME)
# # gemini_secret_val
gemini_creds = json.loads(gemini_secret_val['SecretString'])
gcp_apikey = gemini_creds[GEMINI_SECRET_KEY]
genai.configure(api_key=gcp_apikey)



