from sqlalchemy import Column, String, INT

from app.models.basic import Basic
from app.models.database import Database


class SQLHistory(Basic):
    __tablename__ = "ats_sql_history"
    sql = Column(String(1024), comment="sql语句")
    elapsed = Column(INT, comment="请求耗时")
    database_id = Column(INT, comment="操作数据库id")
    database: Database

    def __init__(self, sql, elapsed, database_id, user):
        super().__init__(user)
        self.sql = sql
        self.elapsed = elapsed
        self.database_id = database_id
