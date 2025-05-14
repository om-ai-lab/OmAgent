from omagent_core.utils.registry import registry
from omagent_core.tool_system.base import ArgSchema, BaseTool
from jupyter_client import KernelManager

ARGSCHEMA = {
    "code": {"type": "string", "description": "Code block to be executed"},
}


@registry.register_tool()
class CodeInterpreter(BaseTool):
    args_schema: ArgSchema = ArgSchema(**ARGSCHEMA)
    description: str = (
        "Python code must be run via this tool, it can be simple code or complex code like deploying web server. Contains libs like numpy, pandas, matplotlib, sklearn, etc. You must print the result to stdout."
    )

    def _run(
        self,
        code: str = None,
    ) -> dict:

        # Choose a kernel name, for example 'python3'
        kernel_name = "python3"

        # Create a KernelManager
        km = KernelManager(kernel_name=kernel_name)
        # Initialize the KernelManager
        km = KernelManager()
        # Start the kernel
        km.start_kernel()
        # Create a client to communicate with the kernel
        kc = km.client()
        # Start the communication channels
        kc.start_channels()

        # Wait until the kernel is ready
        kc.wait_for_ready()

        # Send code to be executed by the kernel
        kc.execute(code)

        # Initialize a dictionary to store the result
        result = {"Error": None, "Output": None}
        print(code)

        try:
            while True:
                # Get messages from the IOPub channel with a timeout of 10 seconds
                msg = kc.get_iopub_msg(timeout=10)
                # Get the type of message
                msg_type = msg["header"]["msg_type"]

                # Check if the message is an execution result
                if msg_type == "execute_result":
                    # Store the output in the result dictionary
                    result["Output"] = msg["content"]["data"]["text/plain"]
                    break
                # Check if the message is a stream message from stdout
                elif msg_type == "stream" and msg["content"]["name"] == "stdout":
                    # Store the output in the result dictionary
                    result["Output"] = msg["content"]["text"]
                    break
                # Check if the message is an error message
                elif msg_type == "error":
                    # Store the error in the result dictionary
                    result["Error"] = msg["content"]["evalue"]
                    break
        except Exception as e:
            # Handle timeout or other exceptions
            result["Error"] = f"Timeout or Error: {str(e)}"

        # Stop the communication channels
        kc.stop_channels()
        # Shutdown the kernel
        km.shutdown_kernel()

        return result

    async def _arun(
        self,
        code: str = None,
    ) -> str:
        result = self._run(code)

        return result
