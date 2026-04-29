from sqlalchemy import delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import (
    Block,
    Favorite,
    Like,
    MatchRequest,
    ProfileView,
    Report,
    User,
    UserReport,
)


async def delete_user_cascade(session: AsyncSession, uid: int) -> None:
    """User va unga aloqador barcha qatorlarni o'chirish.

    MySQL foreign key cheklovlari User'ni o'chirishdan oldin
    bog'liq jadvallar tozalanishini talab qiladi.
    """
    await session.execute(
        delete(MatchRequest).where(
            or_(MatchRequest.sender_id == uid, MatchRequest.receiver_id == uid)
        )
    )
    await session.execute(
        delete(Like).where(or_(Like.from_id == uid, Like.to_id == uid))
    )
    await session.execute(
        delete(Favorite).where(or_(Favorite.user_id == uid, Favorite.target_id == uid))
    )
    await session.execute(
        delete(Block).where(or_(Block.user_id == uid, Block.target_id == uid))
    )
    await session.execute(
        delete(ProfileView).where(
            or_(ProfileView.viewer_id == uid, ProfileView.target_id == uid)
        )
    )
    await session.execute(delete(Report).where(Report.user_id == uid))
    await session.execute(
        delete(UserReport).where(
            or_(UserReport.reporter_id == uid, UserReport.target_id == uid)
        )
    )
    await session.execute(delete(User).where(User.telegram_id == uid))
