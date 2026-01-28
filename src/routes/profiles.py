from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date

from database import get_db
from database.models.accounts import UserModel, UserProfileModel, UserGroupEnum
from schemas.profiles import ProfileResponseSchema
from config.dependencies import get_jwt_auth_manager, get_s3_storage_client
from security.interfaces import JWTAuthManagerInterface
from storages.interfaces import S3StorageInterface
from src.security.http import get_token

router = APIRouter(prefix="/users", tags=["Profiles"])

@router.post("/{user_id}/profile/", response_model=ProfileResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_profile(
    user_id: int,
    first_name: str = Form(...),
    last_name: str = Form(...),
    gender: str = Form(None),
    date_of_birth: date = Form(None),
    info: str = Form(None),
    avatar: UploadFile = File(None),
    db: AsyncSession = Depends(get_db),
    token: str = Depends(get_token),
    auth_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
    s3_client: S3StorageInterface = Depends(get_s3_storage_client)
):
    # 1. Отримуємо дані з токена
    payload = auth_manager.decode_access_token(token)
    current_user_id = int(payload.get("sub"))

    # 2. Отримуємо поточного юзера з бази, щоб перевірити його групу (Admin чи ні)
    current_user_query = await db.execute(
        select(UserModel).where(UserModel.id == current_user_id)
    )
    current_user = current_user_query.scalar_one_or_none()

    # 3. ПЕРЕВІРКА ПРАВ (Authorization)
    if current_user_id != user_id and current_user.group.name != UserGroupEnum.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    # 4. ПЕРЕВІРКА ЦІЛЬОВОГО ЮЗЕРА (401 за вимогами ментора)
    target_user_query = await db.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    target_user = target_user_query.scalar_one_or_none()

    if not target_user or not target_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or not active."
        )

    # 5. ПЕРЕВІРКА НА ДУБЛІКАТ ПРОФІЛЮ
    profile_query = await db.execute(
        select(UserProfileModel).where(UserProfileModel.user_id == user_id)
    )
    if profile_query.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profile already exists")

    # 6. РОБОТА З AVATAR (MinIO)
    avatar_path = None
    if avatar:
        avatar_path = await s3_client.upload_file(avatar)

    # 7. ЗБЕРЕЖЕННЯ
    new_profile = UserProfileModel(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        gender=gender,
        date_of_birth=date_of_birth,
        info=info,
        avatar=avatar_path
    )
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)

    return new_profile
