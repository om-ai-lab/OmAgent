# ltm_text_sql.py

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel
from sqlmodel import SQLModel, create_engine, Session, select, delete
from sqlalchemy import text
from sqlalchemy_utils import create_database, database_exists
from omagent_core.memories.ltms.ltm_base import LTMSQLBase  # Ensure this path is correct
from omagent_core.utils.error import VQLError
from omagent_core.utils.logger import logging


class LTMTextLTM(LTMSQLBase, BaseModel):
    # Database connection parameters
    db: str
    user: str
    passwd: str
    host: str = "localhost"
    port: int = 3306

    # Table and engine
    table: Optional[Any] = None  # Should be a SQLModel subclass
    engine: Optional[Any] = None  # SQLAlchemy engine

    DELETED: int = 1
    NO_DELETED: int = 0

    class Config:
        extra = "allow"
        arbitrary_types_allowed = True

    def __init__(self, **data: Any):
        super().__init__(**data)
        # Initialize the database engine
        if not self.engine:
            self.alchemy_uri = f"mysql+pymysql://{self.user}:{self.passwd}@{self.host}:{self.port}/{self.db}"
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
                # Create the database if it does not exist
                create_database(self.engine.url)
            else:
                # Connect to the existing database
                self.engine.connect()

            # Create tables if they do not exist
            SQLModel.metadata.create_all(bind=self.engine)

    def add_data(
        self,
        data: List[Union[Any, Dict]],
    ) -> List[int]:
        """
        Add data to the knowledge base.

        Args:
            data (List[Union[Any, Dict]]): A list of data entries to add.

        Returns:
            List[int]: A list of IDs of the inserted data.
        """
        data_instances = [
            item if hasattr(item, "__table__") else self.table(**item) for item in data
        ]

        num = 0
        inserted = []
        with Session(self.engine) as session:
            for item in data_instances:
                session.add(item)
                num += 1
                inserted.append(item)
            session.commit()
            print(f"{num} data entries added to table [{self.table.__tablename__}]")
            ids = [item.id for item in inserted]
        return ids

    def match_data(
        self,
        query_data: str,
        bot_id: str,
        size: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Match query data against the knowledge base.

        Args:
            query_data (str): The query string to match.
            bot_id (str): The bot ID to filter data.
            size (int): The number of results to return.

        Returns:
            List[Dict[str, Any]]: A list of matched data entries.
        """
        with Session(self.engine) as session:
            statement = (
                select(self.table)
                .where(self.table.bot_id == bot_id)
                .where(self.table.deleted == self.NO_DELETED)
                .where(self.table.content.like(f"%{query_data}%"))
                .order_by(self.table.id.desc())
                .limit(size)
            )
            results = session.exec(statement).all()

        output = [{"data": result} for result in results]
        return output

    def delete_data(self, ids: List[int]):
        """
        Delete data entries by marking them as deleted.

        Args:
            ids (List[int]): A list of IDs to delete.
        """
        for id in ids:
            self.simple_update(id=id, key="deleted", value=self.DELETED)
            print(f"ID [{id}] marked as deleted in table [{self.table.__tablename__}]")

    def init_memory(self) -> int:
        """
        Initialize the knowledge base by deleting all entries.

        Returns:
            int: The number of rows deleted.
        """
        with Session(self.engine) as session:
            result = session.exec(delete(self.table))
            session.commit()
            del_row_num = result.rowcount
        print(f"Knowledge base initialized. {del_row_num} rows deleted.")
        return del_row_num

    def simple_update(self, id: int, key: str, value: Any):
        """
        Update a specific field of a data entry.

        Args:
            id (int): The ID of the entry to update.
            key (str): The field to update.
            value (Any): The new value for the field.
        """
        with Session(self.engine) as session:
            statement = select(self.table).where(self.table.id == id)
            query_result = session.exec(statement).one_or_none()
            if not query_result:
                raise VQLError(
                    500,
                    detail=f"Trying to update non-existent data [{id}] in table [{self.table.__tablename__}]",
                )
            elif getattr(query_result, "deleted", 0) == self.DELETED:
                raise VQLError(
                    500,
                    detail=f"Trying to update deleted data [{id}] in table [{self.table.__tablename__}]",
                )

            setattr(query_result, key, value)
            session.add(query_result)
            session.commit()
            print(
                f"Key [{key}] in ID [{id}] updated to [{value}] in table [{self.table.__tablename__}]"
            )

    def execute_sql(self, sql_query: str) -> List[Dict[str, Any]]:
        """
        Execute a raw SQL query.

        Args:
            sql_query (str): The SQL query string.

        Returns:
            List[Dict[str, Any]]: A list of results as dictionaries.
        """
        matches = []
        with self.engine.connect() as connection:
            result = connection.execute(text(sql_query))
            for row in result:
                matches.append(dict(row))
        return matches

    def simple_get(self, bot_id: str, number: int = None) -> List[Any]:
        """
        Retrieve data entries for a specific bot ID.

        Args:
            bot_id (str): The bot ID to filter data.
            number (int, optional): The number of entries to retrieve.

        Returns:
            List[Any]: A list of data entries.
        """
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

        return query_results or []

    def get_by_id(self, bot_id: str, id: int) -> Optional[Any]:
        """
        Retrieve a data entry by its ID.

        Args:
            bot_id (str): The bot ID to filter data.
            id (int): The ID of the data entry.

        Returns:
            Optional[Any]: The data entry if found, else None.
        """
        with Session(self.engine) as session:
            statement = (
                select(self.table)
                .where(self.table.bot_id == bot_id)
                .where(self.table.id == id)
                .where(self.table.deleted == self.NO_DELETED)
            )
            query_result = session.exec(statement).one_or_none()
        return query_result

    def text_search(
        self,
        query: str,
        bot_id: str,
        limit: int = 10,
    ) -> List[Any]:
        """
        Perform a text search on the content field.

        Args:
            query (str): The text query.
            bot_id (str): The bot ID to filter data.
            limit (int, optional): The maximum number of results.

        Returns:
            List[Any]: A list of matched data entries.
        """
        with Session(self.engine) as session:
            statement = (
                select(self.table)
                .where(self.table.bot_id == bot_id)
                .where(self.table.deleted == self.NO_DELETED)
                .where(self.table.content.like(f"%{query}%"))
                .order_by(self.table.id.desc())
                .limit(limit)
            )
            results = session.exec(statement).all()
        return results

if __name__ == "__main__":
    from sqlmodel import SQLModel, Field

    class TextData(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        bot_id: str
        content: str
        deleted: int = Field(default=0)

    ltm = LTMTextLTM(
        db='test_db',
        user='test_user',
        passwd='test_password',
        host='localhost',
        port=3306,
        table=TextData
    )
    ltm.init_memory()
    data_to_add = [
        {'bot_id': 'bot123', 'content': 'Hello, how are you?'},
        {'bot_id': 'bot123', 'content': 'Goodbye! See you later.'},
        {'bot_id': 'bot456', 'content': 'Hello from another bot.'},
    ]

    # Add data to the LTM
    inserted_ids = ltm.add_data(data=data_to_add)
    print(f"Inserted IDs: {inserted_ids}")

    # --- Retrieve Data to Verify Insertion ---
    # Retrieve data for bot123
    data_bot123 = ltm.simple_get(bot_id='bot123')
    print("\nData for bot123 after insertion:")
    for item in data_bot123:
        print(f"ID: {item.id}, Content: {item.content}, Deleted: {item.deleted}")

    # --- Delete Data ---
    # IDs to delete
    ids_to_delete = [inserted_ids[0]]  # Delete the first inserted record

    # Delete data from the LTM
    ltm.delete_data(ids=ids_to_delete)
    print(f"\nDeleted IDs: {ids_to_delete}")

    # --- Retrieve Data to Verify Deletion ---
    # Retrieve data for bot123
    data_bot123_after_delete = ltm.simple_get(bot_id='bot123')
    print("\nData for bot123 after deletion:")
    for item in data_bot123_after_delete:
        print(f"ID: {item.id}, Content: {item.content}, Deleted: {item.deleted}")

    # --- Attempt to Match Deleted Data ---
    # Attempt to match the deleted content
    results = ltm.match_data(
        query_data='Hello',
        bot_id='bot123',
        size=10
    )
    print("\nMatch results after deletion:")
    for result in results:
        print(f"ID: {result['data'].id}, Content: {result['data'].content}, Deleted: {result['data'].deleted}")
