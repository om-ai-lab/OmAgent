from typing_extensions import Self


class CreatedAccessKey:
    def __init__(self, id: str, secret: str) -> Self:
        self._id = id
        self._secret = secret

    @property
    def id(self):
        """Gets the id of this CreatedAccessKey.  # noqa: E501

        :return: The id of this CreatedAccessKey.  # noqa: E501
        :rtype: idRef
        """
        return self._id

    @id.setter
    def id(self, id):
        """Sets the id of this CreatedAccessKey.

        :param id: The id of this CreatedAccessKey.  # noqa: E501
        :type: str
        """
        self._id = id

    @property
    def secret(self):
        """Gets the secret of this CreatedAccessKey.  # noqa: E501

        :return: The secret of this CreatedAccessKey.  # noqa: E501
        :rtype: str
        """
        return self._secret

    @secret.setter
    def secret(self, secret):
        """Sets the secret of this CreatedAccessKey.

        :param id: The secret of this CreatedAccessKey.  # noqa: E501
        :type: str
        """
        self._secret = secret

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, CreatedAccessKey):
            return False

        return self.id == other.id and self.secret == other.secret

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
