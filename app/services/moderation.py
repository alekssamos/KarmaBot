from app.models import ModeratorEvent, User, Chat


async def warn_user(moderator: User, target_user: User, chat: Chat, comment: str):
    return await ModeratorEvent.save_new_action(
        moderator=moderator,
        user=target_user,
        chat=chat,
        type_restriction="warn",
        comment=comment
    )


async def cancel_warn(moderator_event_id):
    moderator_event = await ModeratorEvent.get(id_=moderator_event_id)
    if moderator_event.type_restriction == "warn":
        raise ValueError("asked for cancel warn but passed ", moderator_event.type_restriction)
    await moderator_event.delete()


async def ro_user(moderator: User, target_user: User, chat: Chat, comment: str):
    pass
