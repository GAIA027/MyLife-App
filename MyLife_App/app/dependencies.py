from fastapi import Depends, HTTPException, Request, status
from app.modules.MyLife_Tracker import get_current_user_from_token


def get_current_user(request : Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    return get_current_user_from_token(token)


def require_user(current_user=Depends(get_current_user)):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    return current_user

