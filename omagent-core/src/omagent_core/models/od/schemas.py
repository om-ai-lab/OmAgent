from typing import List, Optional

from pydantic import BaseModel


class Target(BaseModel):
    """
    - bbox (List[float]): Bounding box of an object.
    - polygon (List[List[float]]): Polygon of an object.
    - label (str): Object label.
    - conf (float): Object confidence.
    - attr (List[str]): Object attributes.
    """

    bbox: Optional[List[float]] = None
    polygon: Optional[List[List[float]]] = None
    label: Optional[str] = None
    conf: Optional[float] = None
    attr: Optional[List[str]] = None
