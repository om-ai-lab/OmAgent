from typing import Any, Dict, List, Union

from omagent_core.utils.error import VQLError
from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy_utils import create_database, database_exists
from sqlmodel import Session, SQLModel, create_engine, delete, select

from .table import BaseTable


class SQLDataHandler(BaseModel):
    """
    数据库操作基础类
    """

    # 获取数据库相关环境变量
    db: str
    user: str
    passwd: str
    host: str = "localhost"
    port: str = 3306

    table: Any

    DELETED: int = 1
    NO_DELETED: int = 0

    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        arbitrary_types_allowed = True

    def __init__(self, **data: Any) -> None:
        """
        从环境变量，初始化数据库，创建数据库，创建表。
        """
        super().__init__(**data)

        self.alchemy_uri = "mysql+pymysql://%s:%s@%s:%s/%s" % (
            self.user,
            self.passwd,
            self.host,
            self.port,
            self.db,
        )  # 数据库连接url
        self.engine = create_engine(
            self.alchemy_uri,
            pool_pre_ping=True,
            pool_size=50,
            max_overflow=4,
            pool_recycle=7200,
            pool_timeout=600,
            echo=True,
            pool_use_lifo=True,
        )

        if not database_exists(self.engine.url):
            # Create database is not exists
            create_database(self.engine.url)
        else:
            # Connect the database if exists.
            self.engine.connect()

        SQLModel.metadata.create_all(bind=self.engine)

    def execute_sql(self, sql_query: str):
        matches = []
        with self.engine.connect() as connection:
            result = connection.execute(text(sql_query))
            for row in result:
                matches.append(row._asdict())
        return matches

    def simple_get(self, bot_id: str, number: int = None) -> List[BaseTable]:
        with Session(self.engine) as session:
            statement = (
                select(self.table)
                .where(self.table.bot_id == bot_id)
                .where(self.table.deleted == self.NO_DELETED)
                .order_by(self.table.id.desc())
            )
            if number:
                statement = statement.limit(number)
            query_results = session.exec(statement).all()

        if not query_results:
            return []
        return query_results

    def simple_add(self, data: List[Union[BaseTable, Dict]]) -> List[str]:
        """Add data to the table and return ids.

        Args:
            data (List[Union[BaseTable, Dict]]): A list of data you want to add to the table. Could be table objects or valid dicts.

        Returns:
            List[str]: The ids of the inserted rows.
        """
        num = 0
        inserted = []
        with Session(self.engine) as session:
            for item in data:
                if isinstance(item, dict):
                    item = self.table(**item)
                session.add(item)
                num += 1
                inserted.append(item)
            session.commit()
            logging.debug(f"{num} data is added to table [{self.table.__tablename__}]")
            ids = [item.id for item in inserted]
        return ids

    def simple_update(self, id: int, key: str, value: Any):
        with Session(self.engine) as session:
            statement = select(self.table).where(self.table.id == id)
            query_result = session.exec(statement).one()
            if not query_result:
                raise VQLError(
                    500,
                    detail=f"Trying to update non-existent data [{id}] in table [{self.table.__tablename__}]",
                )
            elif query_result.deleted == self.DELETED:
                raise VQLError(
                    500,
                    detail=f"Trying to update deleted data [{id}] in table [{self.table.__tablename__}]",
                )

            query_result.__setattr__(key, value)
            session.add(query_result)
            session.commit()
            logging.debug(
                f"Key [{key}] in id [{id}] is updated to [{value}] in table [{self.table.__tablename__}]"
            )

    def simple_delete(self, id: int):
        self.simple_update(id=id, key="deleted", value=1)
        logging.debug(f"Id [{id}] is deleted in table [{self.table.__tablename__}]")

    def init_table(self):
        with Session(self.engine) as session:
            result = session.exec(delete(self.table))
            session.commit()
            del_row_num = result.rowcount
        return del_row_num
