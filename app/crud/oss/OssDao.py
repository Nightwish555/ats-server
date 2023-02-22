from app.crud import Mapper, ModelWrapper
from app.models.oss_file import OssFile


@ModelWrapper(OssFile)
class OssDao(Mapper):
    pass
