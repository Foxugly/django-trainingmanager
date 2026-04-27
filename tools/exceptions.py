from rest_framework.exceptions import APIException


class ResourceLocked(APIException):
    status_code = 409
    default_detail = "This resource is locked because it is used in multiple places. Clone it to modify."
    default_code = "resource_locked"
