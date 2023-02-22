from app.crud import Mapper, ModelWrapper
from app.models.broadcast_read_user import BroadcastReadUser
from app.utils.logger import Log


@ModelWrapper(BroadcastReadUser, Log("BroadcastReadDao"))
class BroadcastReadDao(Mapper):
    pass
