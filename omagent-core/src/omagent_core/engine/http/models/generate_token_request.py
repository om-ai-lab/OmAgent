import pprint
import re  # noqa: F401

import six


class GenerateTokenRequest(object):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    """
    Attributes:
      swagger_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    swagger_types = {"key_id": "str", "key_secret": "str"}

    attribute_map = {"key_id": "keyId", "key_secret": "keySecret"}

    def __init__(self, key_id=None, key_secret=None):  # noqa: E501
        """GenerateTokenRequest - a model defined in Swagger"""  # noqa: E501
        self._key_id = None
        self._key_secret = None
        self.discriminator = None
        self.key_id = key_id
        self.key_secret = key_secret

    @property
    def key_id(self):
        """Gets the key_id of this GenerateTokenRequest.  # noqa: E501


        :return: The key_id of this GenerateTokenRequest.  # noqa: E501
        :rtype: str
        """
        return self._key_id

    @key_id.setter
    def key_id(self, key_id):
        """Sets the key_id of this GenerateTokenRequest.


        :param key_id: The key_id of this GenerateTokenRequest.  # noqa: E501
        :type: str
        """
        self._key_id = key_id

    @property
    def key_secret(self):
        """Gets the key_secret of this GenerateTokenRequest.  # noqa: E501


        :return: The key_secret of this GenerateTokenRequest.  # noqa: E501
        :rtype: str
        """
        return self._key_secret

    @key_secret.setter
    def key_secret(self, key_secret):
        """Sets the key_secret of this GenerateTokenRequest.


        :param key_secret: The key_secret of this GenerateTokenRequest.  # noqa: E501
        :type: str
        """
        self._key_secret = key_secret

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(
                    map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value)
                )
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(
                    map(
                        lambda item: (
                            (item[0], item[1].to_dict())
                            if hasattr(item[1], "to_dict")
                            else item
                        ),
                        value.items(),
                    )
                )
            else:
                result[attr] = value
        if issubclass(GenerateTokenRequest, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, GenerateTokenRequest):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
