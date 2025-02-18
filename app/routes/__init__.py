import os
from fastapi import Header, HTTPException

api_tokens = os.getenv("API_TOKEN", "123").split(',')


def validate_api_token(api_token: str = Header()):
    if api_token not in api_tokens:
        raise HTTPException(401)
