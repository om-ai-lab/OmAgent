from pathlib import Path
from typing import Any, Dict, Optional, Union

from pydantic import field_validator
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.default import unitree_go_msg_dds__SportModeState_
from unitree_sdk2py.idl.unitree_go.msg.dds_ import SportModeState_
from unitree_sdk2py.go2.sport.sport_client import (
    SportClient,
    PathPoint,
    SPORT_PATH_POINT_SIZE,
)

from ....utils.logger import logging
from ....utils.registry import registry
from ...base import ArgSchema, BaseTool

CURRENT_PATH = Path(__file__).parents[0]

ARGSCHEMA = {
}


@registry.register_tool()
class StandUp(BaseTool):
    """Tool for making Unitree Go2 robot stand up. The robot stands up normally, with the joint motor locked. Compared to the balanced standing mode, this mode does not maintain a constant balance posture. The default standing height is 0.33m."""

    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        arbitrary_types_allowed = True

    args_schema: ArgSchema = ArgSchema(**ARGSCHEMA)
    description: str = "Control the Unitree Go2 robot to stand up. The robot stands up normally, with the joint motor locked. Compared to the balanced standing mode, this mode does not maintain a constant balance posture. The default standing height is 0.33m."
    network_interface_name: Optional[str]

    def __init__(self, **data: Any) -> None:
        """
        Initialize the StandUp tool.
        
        Initializes the base tool with the provided data, configures the channel factory
        with the designated network interface, and sets up a sport client with a timeout
        of 10 seconds for robot communication.
        """
        super().__init__(**data)
        ChannelFactoryInitialize(0, self.network_interface_name)
        self.sport_client = SportClient()  
        self.sport_client.SetTimeout(10.0)
        self.sport_client.Init()

    @field_validator("network_interface_name")
    @classmethod
    def network_interface_name_validator(cls, network_interface_name: Union[str, None]) -> Union[str, None]:
        """
        Validate that a network interface name is provided.
        
        Raises:
            ValueError: If network_interface_name is None.
        
        Returns:
            str: The validated network interface name.
        """
        if network_interface_name == None:
            raise ValueError("network interface name is not provided.")
        return network_interface_name

    def _run(
        self
    ) -> Dict[str, Any]:
        """
        Commands the Unitree Go2 robot to stand up.
        
        Sends the stand-up command through the sport_client and returns a dictionary indicating
        the result. On success, it returns a dictionary with a code of 0 and a message "success".
        If an error occurs, the error is logged and the method returns a dictionary with a code
        of 500 and a message "failed".
        """

        try:
            self.sport_client.StandUp()
            return {
                "code": 0,
                "msg": "success",
            }
        except Exception as e:
            logging.error(f"Stand up failed: {e}")
            return {
                "code": 500,
                "msg": "failed",
            }
