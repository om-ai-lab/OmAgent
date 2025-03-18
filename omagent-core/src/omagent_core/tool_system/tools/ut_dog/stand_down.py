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
class StandDown(BaseTool):
    """Tool for making Unitree Go2 robot stand down. The robot lies down, and the motor joints remain locked."""

    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        arbitrary_types_allowed = True

    args_schema: ArgSchema = ArgSchema(**ARGSCHEMA)
    description: str = "Control the Unitree Go2 robot to stand down. The robot lies down, and the motor joints remain locked."
    network_interface_name: Optional[str]

    def __init__(self, **data: Any) -> None:
        """
        Initializes the StandDown tool and configures its SportClient.
        
        Sets up the base tool using provided keyword arguments, initializes the network
        channel with the specified interface, and prepares a SportClient with a 10-second
        timeout for communication.
        
        Args:
            **data: Arbitrary keyword arguments for tool configuration.
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
        Ensures a network interface name is provided.
        
        Raises:
            ValueError: If no network interface name is provided.
        
        Returns:
            str: The provided network interface name.
        """
        if network_interface_name == None:
            raise ValueError("network interface name is not provided.")
        return network_interface_name

    def _run(
        self
    ) -> Dict[str, Any]:
        """
        Attempts to command the Unitree Go2 robot to stand down.
        
        Returns:
            Dict[str, Any]: A dictionary with the operation's status where "code" is 0 for success 
            and 500 for failure, and "msg" indicates "success" or "failed" accordingly.
        """

        try:
            self.sport_client.StandDown()
            return {
                "code": 0,
                "msg": "success",
            }
        except Exception as e:
            logging.error(f"Stand down failed: {e}")
            return {
                "code": 500,
                "msg": "failed",
            }

if __name__ == "__main__":
    tool = StandDown(network_interface_name="eth0")
    tool.run()