from app.models.database import db
from app.utils.tool import time_now


class UserDao:

    @staticmethod
    async def set_current_user(email: str, username: str):
        ret = await db.table("users").save({
            "email": email,
            "username": username
        })
        if ret['inserted']:
            now = time_now()
            await db.table("users").save(
                {
                    "secretKey": "S:" + str(uuid.uuid4()),
                    "token": str(uuid.uuid4()).replace("-", ""),
                    "createdAt": now,
                    "lastLoggedInAt": now,
                }, ret['id'])
            user_count = await db.table("users").filter({"admin": True}).filter(
                r.row["createdAt"].le(now)).count()  # yapf: disable
            if user_count == 0:
                # set first user as admin
                await db.table("users").save(dict(admin=True), ret['id'])

        elif ret['unchanged']:
            await db.table("users").save({
                "lastLoggedInAt": time_now(),
            }, ret['id'])
