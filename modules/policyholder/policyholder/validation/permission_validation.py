from django.utils.translation import gettext as _
from django.core.exceptions import PermissionDenied


class PermissionValidation:

    @classmethod
    def validate_perms(cls, user, perms):
        if not user.has_perms(perms):
            raise PermissionDenied(_("unauthorized"))
