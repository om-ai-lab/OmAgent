from typing import List

from omagent_core.engine.http.models.target_ref import TargetRef
from typing_extensions import Self


class GrantedPermission:
    def __init__(self, target: TargetRef, access: List[str]) -> Self:
        self._target = target
        self._access = access

    @property
    def target(self):
        """Gets the target of this GrantedPermission.  # noqa: E501


        :return: The target of this GrantedPermission.  # noqa: E501
        :rtype: TargetRef
        """
        return self._target

    @target.setter
    def target(self, target):
        """Sets the target of this GrantedPermission.


        :param target: The target of this GrantedPermission.  # noqa: E501
        :type: TargetRef
        """
        self._target = target

    @property
    def access(self):
        """Gets the access of this GrantedPermission.  # noqa: E501


        :return: The access of this GrantedPermission.  # noqa: E501
        :rtype: List[str]
        """
        return self._access

    @access.setter
    def access(self, access):
        """Sets the access of this GrantedPermission.


        :param target: The access of this GrantedPermission.  # noqa: E501
        :type: List[str]
        """
        self._access = access

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, GrantedPermission):
            return False

        return self.target == other.target and self.access == other.access

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
