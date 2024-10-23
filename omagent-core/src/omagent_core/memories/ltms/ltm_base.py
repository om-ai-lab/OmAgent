from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class LTMVecotrBase(ABC):
    @abstractmethod
    def encoder_register(self, modality: str, encoder: Any):
        """
        Register an encoder for a specific modality.

        Args:
            modality (str): The modality for which the encoder is registered.
            encoder (Any): The encoder object.
        """
        pass

    @abstractmethod
    def add_data(
        self,
        data: List[Dict[str, Any]],
        encode_data: List[Any],
        modality: str,
        src_type: Optional[str] = None,
    ):
        """
        Add data to the knowledge base with vector representations.

        Args:
            data (List[Dict[str, Any]]): The metadata of the data to add.
            encode_data (List[Any]): The actual data used for encoding.
            modality (str): The modality of the data (e.g., 'text', 'image').
            src_type (Optional[str]): The source type of the encode_data.
        """
        pass


    @abstractmethod
    def match_data(
        self,
        query_data: Any,
        modality: str,
        filters: Dict[str, Any] = {},
        threshold: float = 0.0,
        size: int = 1,
        src_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Match query data against the knowledge base.

        Args:
            query_data (Any): The query data to match.
            modality (str): The modality of the query data.
            filters (Dict[str, Any]): Filters to apply during the search.
            threshold (float): The similarity threshold.
            size (int): The number of results to return.
            src_type (Optional[str]): The source type of the query data.

        Returns:
            List[Dict[str, Any]]: A list of matched data with scores and metadata.
        """
        pass

    @abstractmethod
    def delete_data(self, ids: List[str]):
        """
        Delete data entries from the knowledge base.

        Args:
            ids (List[str]): The IDs of the data entries to delete.
        """
        pass

    @abstractmethod
    def init_memory(self, mapping: Optional[Dict[str, Any]] = None):
        """
        Initialize or reset the knowledge base.

        Args:
            mapping (Optional[Dict[str, Any]]): The schema mapping for the knowledge base.
        """
        pass

class LTMSQLBase(ABC):    
    @abstractmethod
    def add_data(
        self,
        data: List[Dict[str, Any]],
        encode_data: List[Any],
        modality: str,
        src_type: Optional[str] = None,
    ):
        """
        Add data to the knowledge base with vector representations.

        Args:
            data (List[Dict[str, Any]]): The metadata of the data to add.
            encode_data (List[Any]): The actual data used for encoding.
            modality (str): The modality of the data (e.g., 'text', 'image').
            src_type (Optional[str]): The source type of the encode_data.
        """
        pass


    @abstractmethod
    def match_data(
        self,
        query_data: Any,
        modality: str,
        filters: Dict[str, Any] = {},
        threshold: float = 0.0,
        size: int = 1,
        src_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Match query data against the knowledge base.

        Args:
            query_data (Any): The query data to match.
            modality (str): The modality of the query data.
            filters (Dict[str, Any]): Filters to apply during the search.
            threshold (float): The similarity threshold.
            size (int): The number of results to return.
            src_type (Optional[str]): The source type of the query data.

        Returns:
            List[Dict[str, Any]]: A list of matched data with scores and metadata.
        """
        pass

    @abstractmethod
    def delete_data(self, ids: List[str]):
        """
        Delete data entries from the knowledge base.

        Args:
            ids (List[str]): The IDs of the data entries to delete.
        """
        pass

    @abstractmethod
    def init_memory(self, mapping: Optional[Dict[str, Any]] = None):
        """
        Initialize or reset the knowledge base.

        Args:
            mapping (Optional[Dict[str, Any]]): The schema mapping for the knowledge base.
        """
        pass
