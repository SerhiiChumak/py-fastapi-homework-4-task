from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db
from database.models.accounts import UserModel, UserProfileModel, GenderEnum
from schemas.profiles import ProfileCreateSchema, ProfileResponseSchema
from config.dependencies import get_accounts_email_notificator, get_jwt_auth_manager, get_s3_storage_client

router = APIRouter(prefix="/profiles", tags=["Profiles"])


@router.post("/", response_model=ProfileResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_profile(
        first_name: str = Form(...),
        last_name: str = Form(...),
        gender: GenderEnum = Form(None),
        date_of_birth: date = Form(None),
        info: str = Form(None),
        avatar: UploadFile = File(None),
        db: AsyncSession = Depends(get_db),
        token: str = Depends(get_accounts_email_notificator),
        auth_manager=Depends(get_jwt_auth_manager),
        s3_client=Depends(get_s3_storage_client)
):
    token_data = auth_manager.decode_access_token(token)
    user_id = int(token_data.get("sub"))

    query = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account not activated")

    query_profile = select(UserProfileModel).where(UserProfileModel.user_id == user_id)
    profile_exists = (await db.execute(query_profile)).scalar_one_or_none()
    if profile_exists:
        raise HTTPException(status_code=400, detail="Profile already exists")

    return {"message"}
