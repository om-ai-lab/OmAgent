from typing import Any, Optional

from pydantic import field_validator
from pymilvus import CollectionSchema, DataType, FieldSchema

from ..models.encoders.base import EncoderBase
from ..utils.registry import registry
from ..utils.error import VQLError
from .milvus_handler import MilvusHandler


@registry.register_handler()
class LTMMilvusHandler(MilvusHandler):
    collection_name: str
    text_encoder: Optional[EncoderBase] = None
    dim: int = None

    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        arbitrary_types_allowed = True

    @field_validator("text_encoder", mode="before")
    @classmethod
    def init_encoder(cls, text_encoder):
        if isinstance(text_encoder, EncoderBase):
            return text_encoder
        elif isinstance(text_encoder, dict):
            return registry.get_encoder(text_encoder.get("name"))(**text_encoder)
        else:
            raise ValueError("text_encoder must be EncoderBase or Dict")

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)

        self.dim = self.text_encoder.dim
        
        schema_dict = data.get('schema', None)
        fields = []
        for field_info in schema_dict['fields']:
            field = FieldSchema(
                name=field_info['name'],
                dtype=self._get_data_type(field_info['dtype']),
                is_primary=field_info.get('is_primary', False),
                auto_id=field_info.get('auto_id', False),
                max_length=field_info.get('max_length', None),
                dim= self.dim if "VECTOR" in field_info['dtype'] else None
            )
            fields.append(field)

        # Create the collection schema        
        collection_schema = CollectionSchema(
            fields=fields,
            description=schema_dict.get('collection_description', ''),
            enable_dynamic_field=schema_dict.get('enable_dynamic_field', False)
        )
               
        self.make_collection(self.collection_name, collection_schema)
    
    def _get_data_type(self, dtype_str):
        return {
            "INT64": DataType.INT64,
            "VARCHAR": DataType.VARCHAR,
            "BOOL": DataType.BOOL,
            "INT8": DataType.INT8,
            "INT16": DataType.INT16,
            "INT32": DataType.INT32,
            "FLOAT": DataType.FLOAT,
            "DOUBLE": DataType.DOUBLE,
            "JSON": DataType.JSON,
            "ARRAY": DataType.ARRAY,
            "BINARY_VECTOR": DataType.BINARY_VECTOR,
            "FLOAT_VECTOR": DataType.FLOAT_VECTOR,
            "FLOAT16_VECTOR": DataType.FLOAT16_VECTOR,
            "BFLOAT16_VECTOR": DataType.BFLOAT16_VECTOR,
            "SPARSE_FLOAT_VECTOR": DataType.SPARSE_FLOAT_VECTOR
        }.get(dtype_str)

    def text_add(self, upload_data:dict, target_field="content"):
        if self.text_encoder is None:
            raise VQLError(500, detail="Missing text_encoder")
        if target_field:
            content_vector = self.text_encoder.infer([upload_data.get('target_field')])[0]
            upload_data[f'{target_field}_vector'] = content_vector        

        add_detail = self.do_add(self.collection_name, upload_data)

    def text_match(
        self,
        content,        
        threshold: float,
        output_fields=["content"],
        filter_expr: str="",
        res_size: int = 100,
        target_field="content"
        
    ):
        content_vector = self.text_encoder.infer([content])[0]
        match_res = self.match(
            collection_name=self.collection_name,
            query_vectors=[content_vector],
            query_field=f"{target_field}_vector",
            output_fields=output_fields,
            res_size=res_size,
            threshold=threshold,
            filter_expr=filter_expr,
        )

        output = []
        for match in match_res[0]:
            print(match)
            output.append(match["entity"])

        return output
