class VQLError(Exception):
    def __init__(self, code, msg=None, detail=""):
        """
        :param code: Error code
        :param msg: Error message, for system display.
        :param detail: Error detail, for debugging.
        """

        code2msg = {
            500: "Internal Error",
            501: "Image Error: Unable to Read",  # Unable to read image file
            502: "Image Error: Corrupted Image",  # Image file is corrupted
            503: "Image Error: Unable to Retrieve",  # Failed to retrieve image
            504: "Image Error: Unrecognized Format",  # Unsupported image file format
            505: "Image Error: Key Not Found",  # Key does not exist when retrieving data in Redis mode
            506: "Image Error: Unable to Connect to Database",  # Unable to connect to Redis when retrieving data in Redis mode
            511: "Request Error: Service Processing Failed",  # Atom error for unknown reasons
            515: "Request Error: Max Retries Exceeded, Unable to Access Address",  # API URL or port error, unable to access
            516: "Request Error: Invalid Address",  # Incorrect API route address
            517: "Request Error: Invalid Request Format",  # Input parameter format error
            518: "Request Error: Illegal Request Address",  # Incorrect format of atom API address
            550: "Vector Database Error",
            570: "Callback Error: Failed to Process Result Callback",  # Error occurred during algorithm result callback
            800: "LLM Error: Unexpected Return Result",  # LLM return result does not meet expectations
        }

        self.code = code
        self.detail = detail
        if msg:
            self.msg = msg
        else:
            self.msg = code2msg[code]

    def __str__(self):
        return repr(
            "Code: {} | message: {} | detail:{}".format(
                self.code, self.msg, self.detail
            )
        )
