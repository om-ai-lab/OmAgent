import pprint
import re  # noqa: F401

import six


class IntegrationApi(object):
    """
    Attributes:
      swagger_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    swagger_types = {
        'api': 'str',
        'configuration': 'dict(str, object)',
        'created_by': 'str',
        'created_on': 'int',
        'description': 'str',
        'enabled': 'bool',
        'integration_name': 'str',
        'tags': 'list[TagObject]',
        'updated_by': 'str',
        'updated_on': 'int'
    }

    attribute_map = {
        'api': 'api',
        'configuration': 'configuration',
        'created_by': 'createdBy',
        'created_on': 'createdOn',
        'description': 'description',
        'enabled': 'enabled',
        'integration_name': 'integrationName',
        'tags': 'tags',
        'updated_by': 'updatedBy',
        'updated_on': 'updatedOn'
    }

    def __init__(self, api=None, configuration=None, created_by=None, created_on=None, description=None, enabled=None,
                 integration_name=None, tags=None, updated_by=None, updated_on=None):  # noqa: E501
        """IntegrationApi - a model defined in Swagger"""  # noqa: E501
        self._api = None
        self._configuration = None
        self._created_by = None
        self._created_on = None
        self._description = None
        self._enabled = None
        self._integration_name = None
        self._tags = None
        self._updated_by = None
        self._updated_on = None
        self.discriminator = None
        if api is not None:
            self.api = api
        if configuration is not None:
            self.configuration = configuration
        if created_by is not None:
            self.created_by = created_by
        if created_on is not None:
            self.created_on = created_on
        if description is not None:
            self.description = description
        if enabled is not None:
            self.enabled = enabled
        if integration_name is not None:
            self.integration_name = integration_name
        if tags is not None:
            self.tags = tags
        if updated_by is not None:
            self.updated_by = updated_by
        if updated_on is not None:
            self.updated_on = updated_on

    @property
    def api(self):
        """Gets the api of this IntegrationApi.  # noqa: E501


        :return: The api of this IntegrationApi.  # noqa: E501
        :rtype: str
        """
        return self._api

    @api.setter
    def api(self, api):
        """Sets the api of this IntegrationApi.


        :param api: The api of this IntegrationApi.  # noqa: E501
        :type: str
        """

        self._api = api

    @property
    def configuration(self):
        """Gets the configuration of this IntegrationApi.  # noqa: E501


        :return: The configuration of this IntegrationApi.  # noqa: E501
        :rtype: dict(str, object)
        """
        return self._configuration

    @configuration.setter
    def configuration(self, configuration):
        """Sets the configuration of this IntegrationApi.


        :param configuration: The configuration of this IntegrationApi.  # noqa: E501
        :type: dict(str, object)
        """

        self._configuration = configuration

    @property
    def created_by(self):
        """Gets the created_by of this IntegrationApi.  # noqa: E501


        :return: The created_by of this IntegrationApi.  # noqa: E501
        :rtype: str
        """
        return self._created_by

    @created_by.setter
    def created_by(self, created_by):
        """Sets the created_by of this IntegrationApi.


        :param created_by: The created_by of this IntegrationApi.  # noqa: E501
        :type: str
        """

        self._created_by = created_by

    @property
    def created_on(self):
        """Gets the created_on of this IntegrationApi.  # noqa: E501


        :return: The created_on of this IntegrationApi.  # noqa: E501
        :rtype: int
        """
        return self._created_on

    @created_on.setter
    def created_on(self, created_on):
        """Sets the created_on of this IntegrationApi.


        :param created_on: The created_on of this IntegrationApi.  # noqa: E501
        :type: int
        """

        self._created_on = created_on

    @property
    def description(self):
        """Gets the description of this IntegrationApi.  # noqa: E501


        :return: The description of this IntegrationApi.  # noqa: E501
        :rtype: str
        """
        return self._description

    @description.setter
    def description(self, description):
        """Sets the description of this IntegrationApi.


        :param description: The description of this IntegrationApi.  # noqa: E501
        :type: str
        """

        self._description = description

    @property
    def enabled(self):
        """Gets the enabled of this IntegrationApi.  # noqa: E501


        :return: The enabled of this IntegrationApi.  # noqa: E501
        :rtype: bool
        """
        return self._enabled

    @enabled.setter
    def enabled(self, enabled):
        """Sets the enabled of this IntegrationApi.


        :param enabled: The enabled of this IntegrationApi.  # noqa: E501
        :type: bool
        """

        self._enabled = enabled

    @property
    def integration_name(self):
        """Gets the integration_name of this IntegrationApi.  # noqa: E501


        :return: The integration_name of this IntegrationApi.  # noqa: E501
        :rtype: str
        """
        return self._integration_name

    @integration_name.setter
    def integration_name(self, integration_name):
        """Sets the integration_name of this IntegrationApi.


        :param integration_name: The integration_name of this IntegrationApi.  # noqa: E501
        :type: str
        """

        self._integration_name = integration_name

    @property
    def tags(self):
        """Gets the tags of this IntegrationApi.  # noqa: E501


        :return: The tags of this IntegrationApi.  # noqa: E501
        :rtype: list[TagObject]
        """
        return self._tags

    @tags.setter
    def tags(self, tags):
        """Sets the tags of this IntegrationApi.


        :param tags: The tags of this IntegrationApi.  # noqa: E501
        :type: list[TagObject]
        """

        self._tags = tags

    @property
    def updated_by(self):
        """Gets the updated_by of this IntegrationApi.  # noqa: E501


        :return: The updated_by of this IntegrationApi.  # noqa: E501
        :rtype: str
        """
        return self._updated_by

    @updated_by.setter
    def updated_by(self, updated_by):
        """Sets the updated_by of this IntegrationApi.


        :param updated_by: The updated_by of this IntegrationApi.  # noqa: E501
        :type: str
        """

        self._updated_by = updated_by

    @property
    def updated_on(self):
        """Gets the updated_on of this IntegrationApi.  # noqa: E501


        :return: The updated_on of this IntegrationApi.  # noqa: E501
        :rtype: int
        """
        return self._updated_on

    @updated_on.setter
    def updated_on(self, updated_on):
        """Sets the updated_on of this IntegrationApi.


        :param updated_on: The updated_on of this IntegrationApi.  # noqa: E501
        :type: int
        """

        self._updated_on = updated_on

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value
        if issubclass(IntegrationApi, dict):
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
        if not isinstance(other, IntegrationApi):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
