from django_auth_ldap.backend import populate_user
from django.dispatch import receiver


@receiver(populate_user)
def on_populate_user(sender, **kwargs):
    """Process population of a user."""
    user = kwargs.get('user', None)
    ldap_user = kwargs.get('ldap_user', None)

    if not (user and ldap_user):
        return

    # If the user has a zimbra status and it's not enabled,
    # disable the account
    try:
        zimbra_status = ldap_user.attrs['zimbramailstatus'][0]
    except (KeyError, AttributeError, IndexError):
        zimbra_status = None

    if zimbra_status is not None:
        user.is_active = zimbra_status == 'enabled'

    # Since we're populating from LDAP, disable regular regular password
    user.set_unusable_password()
