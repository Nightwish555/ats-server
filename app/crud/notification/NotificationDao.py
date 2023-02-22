from datetime import timedelta, datetime
from typing import List

from sqlalchemy import select, and_, or_, update

from app.crud import Mapper, ModelWrapper
from app.enums.MessageEnum import MessageTypeEnum, MessageStateEnum
from app.models import async_session
from app.models.broadcast_read_user import BroadcastReadUser
from app.models.notification import Notification


@ModelWrapper(Notification)
class NotificationDao(Mapper):

    @classmethod
    async def list_messages(cls, msg_type: int, msg_status: int, receiver: int):
        """
        根据消息id和消息类型以及接收人获取消息数据
        :param msg_type:
        :param msg_status:
        :param receiver:
        :return:
        """
        ninety_days = datetime.now() - timedelta(days=90)
        # 1. 当消息类型不为广播类型时，正常查询
        if msg_type == MessageTypeEnum.others:
            ans = await cls.select_list(msg_status=msg_status, receiver=receiver, msg_type=msg_type,
                                        condition=[Notification.created_at > ninety_days])
        else:
            # 否则需要根据是否已读进行查询 只支持90天内数据
            async with async_session() as session:
                # 找到3个月内的消息
                default_condition = [Notification.deleted_at == 0, Notification.created_at >= ninety_days]
                if msg_type == MessageTypeEnum.broadcast:
                    conditions = [*default_condition, Notification.msg_type == msg_type]
                else:
                    # 说明是全部消息
                    conditions = [*default_condition,
                                  or_(Notification.msg_type == MessageTypeEnum.broadcast.value,
                                      and_(Notification.msg_type == MessageTypeEnum.others.value,
                                           Notification.receiver == receiver))]
                sql = select(Notification, BroadcastReadUser) \
                    .outerjoin(BroadcastReadUser,
                               and_(Notification.id == BroadcastReadUser.notification_id,
                                    BroadcastReadUser.read_user == receiver)).where(*conditions).order_by(
                    Notification.created_at.desc())
                query = await session.execute(sql)
                result = query.all()
                ans = []
                last_month = datetime.now() - timedelta(days=30)
                for notify, read in result:
                    # 如果非广播类型，直接
                    if notify.msg_type == MessageTypeEnum.others:
                        if notify.msg_status == msg_status:
                            ans.append(notify)
                            continue
                    else:
                        if msg_status == MessageStateEnum.read:
                            if read is not None or notify.updated_at < last_month:
                                ans.append(notify)
                        else:
                            if not read:
                                ans.append(notify)
        return ans

    @classmethod
    async def delete_message(cls, session, msg_id: List[int], receiver: int):
        async with session.begin():
            await session.execute(
                update(Notification).where(
                    Notification.id.in_(msg_id),
                    Notification.receiver == receiver,
                    Notification.deleted_at == 0)) \
                .values(
                deleted_at=0,
                updated_at=datetime.now(),
                update_user=receiver)
