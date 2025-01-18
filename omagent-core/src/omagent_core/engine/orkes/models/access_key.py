from omagent_core.engine.orkes.models.access_key_status import AccessKeyStatus
from typing_extensions import Self


class AccessKey:
    def __init__(self, id: str, status: AccessKeyStatus, created_at: int) -> Self:
        self._id = id
        self._status = status
        self._created_at = created_at

        if self._status is None:
            self._status = AccessKeyStatus.ACTIVE

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
    def status(self):
        """Gets the status of this CreatedAccessKey.  # noqa: E501

        :return: The status of this CreatedAccessKey.  # noqa: E501
        :rtype: str
        """
        return self._status

    @status.setter
    def status(self, status):
        """Sets the status of this CreatedAccessKey.

        :param id: The status of this CreatedAccessKey.  # noqa: E501
        :type: str
        """
        self._status = status

    @property
    def created_at(self):
        """Gets the created_at of this CreatedAccessKey.  # noqa: E501

        :return: The created_at of this CreatedAccessKey.  # noqa: E501
        :rtype: int
        """
        return self._created_at

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, AccessKey):
            return False

        return self.id == other.id and self.status == other.status

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
