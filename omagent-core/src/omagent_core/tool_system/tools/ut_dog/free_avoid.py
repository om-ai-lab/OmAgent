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
    "switch": {
        "type": "bool",
        "description": "switch to enable or disable free avoid.",
        "required": True,
    },
}


@registry.register_tool()
class FreeAvoid(BaseTool):
    """Tool for making Unitree Go2 robot to enable or disable free avoid."""

    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        arbitrary_types_allowed = True

    args_schema: ArgSchema = ArgSchema(**ARGSCHEMA)
    description: str = "Control the Unitree Go2 robot to enable or disable free avoid."
    network_interface_name: Optional[str]

    def __init__(self, **data: Any) -> None:
        """
        Initialize a FreeAvoid instance with communication channel and client.
        
        This method initializes the base class with any provided keyword arguments,
        sets up the communication channel via ChannelFactoryInitialize using the instance's
        network interface, and configures a SportClient with a 10-second timeout before
        finalizing its initialization.
          
        Args:
            **data: Additional keyword arguments for tool configuration.
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
        Validates that a network interface name is provided.
        
        Checks that the given network interface name is not None. Raises a ValueError if no name is provided,
        otherwise returns the network interface name.
        """
        if network_interface_name == None:
            raise ValueError("network interface name is not provided.")
        return network_interface_name

    def _run(
        self,
        switch: bool = True
    ) -> Dict[str, Any]:
        """
        Executes the free avoid command on the Unitree Go2 robot.
        
        This method sends a command to control the robot's free avoid behavior using the sport_client. The provided switch flag determines whether to enable (True) or disable (False) free avoid. On success, it returns a dictionary with a success code and message; if an exception occurs, it logs the error and returns a failure dictionary.
        
        Args:
            switch (bool): True to enable free avoid, False to disable it.
        
        Returns:
            dict: A dictionary containing a status code and message indicating the outcome.
        """

        try:
            self.sport_client.FreeAvoid(switch)
            return {
                "code": 0,
                "msg": "success",
            }
        except Exception as e:
            logging.error(f"Free avoid failed: {e}")
            return {
                "code": 500,
                "msg": "failed",
            }
