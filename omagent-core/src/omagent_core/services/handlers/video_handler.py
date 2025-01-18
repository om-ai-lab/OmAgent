from typing import Any, Optional

from omagent_core.models.encoders.base import EncoderBase
from omagent_core.utils.error import VQLError
from omagent_core.utils.registry import registry
from pydantic import field_validator
from pymilvus import CollectionSchema, DataType, FieldSchema

from .milvus_handler import MilvusHandler


@registry.register_component()
class VideoHandler(MilvusHandler):
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

        _uid = FieldSchema(
            name="_uid", dtype=DataType.INT64, is_primary=True, auto_id=True
        )
        video_md5 = FieldSchema(
            name="video_md5", dtype=DataType.VARCHAR, max_length=100
        )
        content = FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535)
        content_vector = FieldSchema(
            name="content_vector", dtype=DataType.FLOAT_VECTOR, dim=self.dim
        )
        start_time = FieldSchema(
            name="start_time",
            dtype=DataType.FLOAT,
        )
        end_time = FieldSchema(
            name="end_time",
            dtype=DataType.FLOAT,
        )
        schema = CollectionSchema(
            fields=[_uid, video_md5, content, content_vector, start_time, end_time],
            description="video summary vector DB",
            enable_dynamic_field=True,
        )
        self.make_collection(self.collection_name, schema)

    def text_add(self, video_md5, content, start_time, end_time):

        if self.text_encoder is None:
            raise VQLError(500, detail="Missing text_encoder")
        content_vector = self.text_encoder.infer([content])[0]

        # upload_data = [
        #     [video_md5],
        #     [content],
        #     [content_vector],
        #     [start_time],
        #     [end_time],
        # ]
        upload_data = [
            {
                "video_md5": video_md5,
                "content": content,
                "content_vector": content_vector,
                "start_time": start_time,
                "end_time": end_time,
            }
        ]

        add_detail = self.do_add(self.collection_name, upload_data)
        # assert add_detail.succ_count == len(upload_data)

    def text_match(
        self,
        video_md5,
        content,
        threshold: float,
        start_time=None,
        end_time=None,
        res_size: int = 100,
    ):
        # search_query = {"size": res_size, "sort": [{"_score": "desc"}],
        #                 "include": ["content", "start_time", "end_time"]}
        filter_expr = ""
        if video_md5 is not None:
            filter_expr = f"video_md5=='{video_md5}'"
        if start_time is not None and end_time is not None:
            filter_expr += f" and (start_time>={max(0, start_time - 10)} and end_time<={end_time + 10})"
        elif start_time is not None:
            filter_expr += f" and start_time>={max(0, start_time - 10)}"
        elif end_time is not None:
            filter_expr += f" and end_time<={end_time + 10}"
        # text retrieve stage
        content_vector = self.text_encoder.infer([content])[0]
        match_res = self.match(
            collection_name=self.collection_name,
            query_vectors=[content_vector],
            query_field="content_vector",
            output_fields=["content", "start_time", "end_time"],
            res_size=res_size,
            threshold=threshold,
            filter_expr=filter_expr,
        )

        output = []
        for match in match_res[0]:
            print(match)
            output.append(match["entity"])

        return output
