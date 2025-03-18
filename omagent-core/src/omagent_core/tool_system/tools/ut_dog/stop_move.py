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
class StopMove(BaseTool):
    """Tool for making Unitree Go2 robot stop move. This operation will stop the current motion and reset the motion command to the default value."""

    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        arbitrary_types_allowed = True

    args_schema: ArgSchema = ArgSchema(**ARGSCHEMA)
    description: str = "Control the Unitree Go2 robot to stop move. This operation will stop the current motion and reset the motion command to the default value."
    network_interface_name: Optional[str]

    def __init__(self, **data: Any) -> None:
        """
        Initializes the StopMove tool instance.
        
        Calls the parent initializer with provided data, configures the network channel using the
        specified network interface, and sets up the SportClient with a 10-second timeout.
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
            ValueError: If the network interface name is None.
        
        Returns:
            str: The validated network interface name.
        """
        if network_interface_name == None:
            raise ValueError("network interface name is not provided.")
        return network_interface_name

    def _run(
        self,
    ) -> Dict[str, Any]:
        """
        Stops the robot's movement.
        
        Attempts to issue a stop command via the sport client. If successful, returns a
        dictionary with a status code of 0 and a "success" message. If an error occurs,
        logs the error and returns a dictionary with a status code of 500 and a "failed" message.
        """

        try:
            self.sport_client.StopMove()
            return {
                "code": 0,
                "msg": "success",
            }
        except Exception as e:
            logging.error(f"Stop move failed: {e}")
            return {
                "code": 500,
                "msg": "failed",
            }
