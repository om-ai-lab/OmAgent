from typing import Any, Dict, List
from omagent_core.memories.ltms.ltm_vector_milvus import VectorMilvusLTM
from omagent_core.memories.ltms.ltm_vector_pinecone import VectorPineconeLTM
from omagent_core.utils.registry import registry


class LTM:
    def __init__(self, ltm_configs: List[Dict[str, Any]]) -> None:
        """
        Initialize LTM instances based on the provided configurations.

        Args:
            ltm_configs (List[Dict[str, Any]]): List of configurations for LTMs.
        """
        self.ltms = {}
        for config in ltm_configs:
            ltm_name = config['name']
            ltm_type = config.get('ltm_type', 'milvus')  # default to 'milvus'

            if ltm_type == 'milvus':
                ltm_instance = self._create_milvus_ltm(config)
            elif ltm_type == 'pinecone':
                ltm_instance = self._create_pinecone_ltm(config)
            else:
                raise ValueError(f"Unknown LTM type: {ltm_type}")

            # Initialize memory
            try:
                dim = config['text_encoder']['dim']
            except:
                raise ValueError(f"the 'dim' is missing at 'text_encoder' config")

            ltm_instance.init_memory(dim=dim)

            self.ltms[ltm_name] = ltm_instance

    def _create_milvus_ltm(self, config: Dict[str, Any]) -> VectorMilvusLTM:
        """
        Create an instance of VectorMilvusLTM based on the configuration.

        Args:
            config (Dict[str, Any]): Configuration for the Milvus LTM.

        Returns:
            VectorMilvusLTM: An instance of VectorMilvusLTM.
        """
        index_id = config['collection_name']
        from pymilvus import MilvusClient

        milvus_client = MilvusClient(
            uri=config['host_url'],
            user=config['user'],
            password=config['password'],
            db_name=config['db_name'],
        )
        ltm_instance = VectorMilvusLTM(index_id=index_id, milvus_client=milvus_client)
        return ltm_instance

    def _create_pinecone_ltm(self, config: Dict[str, Any]) -> VectorPineconeLTM:
        """
        Create an instance of VectorPineconeLTM based on the configuration.

        Args:
            config (Dict[str, Any]): Configuration for the Pinecone LTM.

        Returns:
            VectorPineconeLTM: An instance of VectorPineconeLTM.
        """
        index_id = config['collection_name']
        import pinecone

        pinecone.init(api_key=config['api_key'], environment=config['environment'])
        pinecone_client = pinecone.Index(index_id)
        ltm_instance = VectorPineconeLTM(index_id=index_id, pinecone_client=pinecone_client)
        return ltm_instance

    def handler_register(self, name: str, handler: Any) -> None:
        """
        Register a handler (e.g., encoder) to the LTM instance.

        Args:
            name (str): Name of the LTM instance.
            handler (Any): Handler to be registered.

        Raises:
            ValueError: If LTM instance with the given name is not found.
        """
        if name in self.ltms:
            ltm_instance = self.ltms[name]
            # Assuming handler is an encoder; you may need to adjust modality based on your use case
            ltm_instance.encoder_register(modality='text', encoder=handler)
        else:
            raise ValueError(f"LTM instance with name '{name}' not found")
