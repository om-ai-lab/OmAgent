from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from omagent_core.engine.http.models.conductor_application import \
    ConductorApplication
from omagent_core.engine.http.models.conductor_user import ConductorUser
from omagent_core.engine.http.models.create_or_update_application_request import \
    CreateOrUpdateApplicationRequest
from omagent_core.engine.http.models.group import Group
from omagent_core.engine.http.models.subject_ref import SubjectRef
from omagent_core.engine.http.models.target_ref import TargetRef
from omagent_core.engine.http.models.upsert_group_request import \
    UpsertGroupRequest
from omagent_core.engine.http.models.upsert_user_request import \
    UpsertUserRequest
from omagent_core.engine.orkes.models.access_key import AccessKey
from omagent_core.engine.orkes.models.access_type import AccessType
from omagent_core.engine.orkes.models.created_access_key import \
    CreatedAccessKey
from omagent_core.engine.orkes.models.granted_permission import \
    GrantedPermission
from omagent_core.engine.orkes.models.metadata_tag import MetadataTag


class AuthorizationClient(ABC):
    # Applications
    @abstractmethod
    def create_application(
        self, create_or_update_application_request: CreateOrUpdateApplicationRequest
    ) -> ConductorApplication:
        pass

    @abstractmethod
    def get_application(self, application_id: str) -> ConductorApplication:
        pass

    @abstractmethod
    def list_applications(self) -> List[ConductorApplication]:
        pass

    @abstractmethod
    def update_application(
        self,
        create_or_update_application_request: CreateOrUpdateApplicationRequest,
        application_id: str,
    ) -> ConductorApplication:
        pass

    @abstractmethod
    def delete_application(self, application_id: str):
        pass

    @abstractmethod
    def add_role_to_application_user(self, application_id: str, role: str):
        pass

    @abstractmethod
    def remove_role_from_application_user(self, application_id: str, role: str):
        pass

    @abstractmethod
    def set_application_tags(self, tags: List[MetadataTag], application_id: str):
        pass

    @abstractmethod
    def get_application_tags(self, application_id: str) -> List[MetadataTag]:
        pass

    @abstractmethod
    def delete_application_tags(self, tags: List[MetadataTag], application_id: str):
        pass

    @abstractmethod
    def create_access_key(self, application_id: str) -> CreatedAccessKey:
        pass

    @abstractmethod
    def get_access_keys(self, application_id: str) -> List[AccessKey]:
        pass

    @abstractmethod
    def toggle_access_key_status(self, application_id: str, key_id: str) -> AccessKey:
        pass

    @abstractmethod
    def delete_access_key(self, application_id: str, key_id: str):
        pass

    # Users
    @abstractmethod
    def upsert_user(
        self, upsert_user_request: UpsertUserRequest, user_id: str
    ) -> ConductorUser:
        pass

    @abstractmethod
    def get_user(self, user_id: str) -> ConductorUser:
        pass

    @abstractmethod
    def list_users(self, apps: Optional[bool] = False) -> List[ConductorUser]:
        pass

    @abstractmethod
    def delete_user(self, user_id: str):
        pass

    # Groups
    @abstractmethod
    def upsert_group(
        self, upsert_group_request: UpsertGroupRequest, group_id: str
    ) -> Group:
        pass

    @abstractmethod
    def get_group(self, group_id: str) -> Group:
        pass

    @abstractmethod
    def list_groups(self) -> List[Group]:
        pass

    @abstractmethod
    def delete_group(self, group_id: str):
        pass

    @abstractmethod
    def add_user_to_group(self, group_id: str, user_id: str):
        pass

    @abstractmethod
    def get_users_in_group(self, group_id: str) -> List[ConductorUser]:
        pass

    @abstractmethod
    def remove_user_from_group(self, group_id: str, user_id: str):
        pass

    # Permissions
    @abstractmethod
    def grant_permissions(
        self, subject: SubjectRef, target: TargetRef, access: List[AccessType]
    ):
        pass

    @abstractmethod
    def get_permissions(self, target: TargetRef) -> Dict[str, List[SubjectRef]]:
        pass

    @abstractmethod
    def get_granted_permissions_for_group(
        self, group_id: str
    ) -> List[GrantedPermission]:
        pass

    @abstractmethod
    def get_granted_permissions_for_user(self, user_id: str) -> List[GrantedPermission]:
        pass

    @abstractmethod
    def remove_permissions(
        self, subject: SubjectRef, target: TargetRef, access: List[AccessType]
    ):
        pass
