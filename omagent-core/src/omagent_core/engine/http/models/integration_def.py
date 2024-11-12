import pprint
import re  # noqa: F401

import six


class IntegrationDef(object):
    """
    Attributes:
      swagger_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    swagger_types = {
        'category': 'str',
        'category_label': 'str',
        'configuration': 'dict(str, object)',
        'description': 'str',
        'enabled': 'bool',
        'icon_name': 'str',
        'name': 'str',
        'tags': 'list[str]',
        'type': 'str'
    }

    attribute_map = {
        'category': 'category',
        'category_label': 'categoryLabel',
        'configuration': 'configuration',
        'description': 'description',
        'enabled': 'enabled',
        'icon_name': 'iconName',
        'name': 'name',
        'tags': 'tags',
        'type': 'type'
    }

    def __init__(self, category=None, category_label=None, configuration=None, description=None, enabled=None,
                 icon_name=None, name=None, tags=None, type=None):  # noqa: E501
        """IntegrationDef - a model defined in Swagger"""  # noqa: E501
        self._category = None
        self._category_label = None
        self._configuration = None
        self._description = None
        self._enabled = None
        self._icon_name = None
        self._name = None
        self._tags = None
        self._type = None
        self.discriminator = None
        if category is not None:
            self.category = category
        if category_label is not None:
            self.category_label = category_label
        if configuration is not None:
            self.configuration = configuration
        if description is not None:
            self.description = description
        if enabled is not None:
            self.enabled = enabled
        if icon_name is not None:
            self.icon_name = icon_name
        if name is not None:
            self.name = name
        if tags is not None:
            self.tags = tags
        if type is not None:
            self.type = type

    @property
    def category(self):
        """Gets the category of this IntegrationDef.  # noqa: E501


        :return: The category of this IntegrationDef.  # noqa: E501
        :rtype: str
        """
        return self._category

    @category.setter
    def category(self, category):
        """Sets the category of this IntegrationDef.


        :param category: The category of this IntegrationDef.  # noqa: E501
        :type: str
        """
        allowed_values = ["API", "AI_MODEL", "VECTOR_DB", "RELATIONAL_DB"]  # noqa: E501
        if category not in allowed_values:
            raise ValueError(
                "Invalid value for `category` ({0}), must be one of {1}"  # noqa: E501
                .format(category, allowed_values)
            )

        self._category = category

    @property
    def category_label(self):
        """Gets the category_label of this IntegrationDef.  # noqa: E501


        :return: The category_label of this IntegrationDef.  # noqa: E501
        :rtype: str
        """
        return self._category_label

    @category_label.setter
    def category_label(self, category_label):
        """Sets the category_label of this IntegrationDef.


        :param category_label: The category_label of this IntegrationDef.  # noqa: E501
        :type: str
        """

        self._category_label = category_label

    @property
    def configuration(self):
        """Gets the configuration of this IntegrationDef.  # noqa: E501


        :return: The configuration of this IntegrationDef.  # noqa: E501
        :rtype: dict(str, object)
        """
        return self._configuration

    @configuration.setter
    def configuration(self, configuration):
        """Sets the configuration of this IntegrationDef.


        :param configuration: The configuration of this IntegrationDef.  # noqa: E501
        :type: dict(str, object)
        """

        self._configuration = configuration

    @property
    def description(self):
        """Gets the description of this IntegrationDef.  # noqa: E501


        :return: The description of this IntegrationDef.  # noqa: E501
        :rtype: str
        """
        return self._description

    @description.setter
    def description(self, description):
        """Sets the description of this IntegrationDef.


        :param description: The description of this IntegrationDef.  # noqa: E501
        :type: str
        """

        self._description = description

    @property
    def enabled(self):
        """Gets the enabled of this IntegrationDef.  # noqa: E501


        :return: The enabled of this IntegrationDef.  # noqa: E501
        :rtype: bool
        """
        return self._enabled

    @enabled.setter
    def enabled(self, enabled):
        """Sets the enabled of this IntegrationDef.


        :param enabled: The enabled of this IntegrationDef.  # noqa: E501
        :type: bool
        """

        self._enabled = enabled

    @property
    def icon_name(self):
        """Gets the icon_name of this IntegrationDef.  # noqa: E501


        :return: The icon_name of this IntegrationDef.  # noqa: E501
        :rtype: str
        """
        return self._icon_name

    @icon_name.setter
    def icon_name(self, icon_name):
        """Sets the icon_name of this IntegrationDef.


        :param icon_name: The icon_name of this IntegrationDef.  # noqa: E501
        :type: str
        """

        self._icon_name = icon_name

    @property
    def name(self):
        """Gets the name of this IntegrationDef.  # noqa: E501


        :return: The name of this IntegrationDef.  # noqa: E501
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this IntegrationDef.


        :param name: The name of this IntegrationDef.  # noqa: E501
        :type: str
        """

        self._name = name

    @property
    def tags(self):
        """Gets the tags of this IntegrationDef.  # noqa: E501


        :return: The tags of this IntegrationDef.  # noqa: E501
        :rtype: list[str]
        """
        return self._tags

    @tags.setter
    def tags(self, tags):
        """Sets the tags of this IntegrationDef.


        :param tags: The tags of this IntegrationDef.  # noqa: E501
        :type: list[str]
        """

        self._tags = tags

    @property
    def type(self):
        """Gets the type of this IntegrationDef.  # noqa: E501


        :return: The type of this IntegrationDef.  # noqa: E501
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type):
        """Sets the type of this IntegrationDef.


        :param type: The type of this IntegrationDef.  # noqa: E501
        :type: str
        """

        self._type = type

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
        if issubclass(IntegrationDef, dict):
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
        if not isinstance(other, IntegrationDef):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
