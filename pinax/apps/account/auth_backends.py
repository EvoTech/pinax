from django.conf import settings

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class AuthenticationBackend(ModelBackend):

    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False

    def authenticate(self, **credentials):
        lookup_params = {}
        if settings.ACCOUNT_EMAIL_AUTHENTICATION:
            name, identity = "email", credentials.get("email")
        else:
            name, identity = "username", credentials.get("username")
        if identity is None:
            return None
        lookup_params[name] = identity
        try:
            user = User.objects.get(**lookup_params)
        except User.DoesNotExist:
            return None
        else:
            if user.check_password(credentials["password"]):
                return user

    def has_perm(self, user_obj, perm, obj=None):

        # @@@ allow all users to add wiki pages
        wakawaka_perms = [
            "wakawaka.add_wikipage",
            "wakawaka.add_revision",
            "wakawaka.change_wikipage",
            "wakawaka.change_revision"
        ]
        if perm in wakawaka_perms:
            return True
        return super(AuthenticationBackend, self).has_perm(user_obj, perm)

EmailModelBackend = AuthenticationBackend


class ObjectPermissionBackend(ModelBackend):
    """Per object level permission backend."""

    supports_object_permissions = True
    supports_anonymous_user = True
    supports_inactive_user = True

    def authenticate(self, username, password):
        return None

    def has_perm(self, user_obj, perm, obj=None):
        """This method checks if the user_obj has perm on obj.

        Returns True or False
        """

        if obj and '.' not in perm and hasattr(obj, '_meta'):
            perm = '{app}.{perm}_{mod}'.format(
                app=obj._meta.app_label,
                perm=perm,
                mod=obj._meta.module_name
            )

        if obj and hasattr(obj, 'is_allowed'):
            try:
                return obj.is_allowed(user_obj, perm=perm)
            except:
                pass
        else:
            return super(ObjectPermissionBackend, self).has_perm(user_obj, perm)
        # Djongo's permission system used only for staff in this project.
        # So, lets check a permission here.
        # It's need, because ModelBackend.has_perm() does not checks access
        # in cases when object is given and it's not None
        return super(ObjectPermissionBackend, self).has_perm(user_obj, perm)
