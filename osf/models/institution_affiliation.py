from django.db import models

from osf.models.base import BaseModel
from osf.models.validators import validate_email
from osf.utils.datetime_aware_jsonfield import DateTimeAwareJSONField
from osf.utils.fields import LowercaseEmailField


class InstitutionAffiliation(BaseModel):

    DEFAULT_VALUE_FOR_SSO_IDENTITY_NOT_AVAILABLE = 'SSO_IDENTITY_NOT_AVAILABLE'

    user = models.ForeignKey('OSFUser', on_delete=models.CASCADE)
    institution = models.ForeignKey('Institution', on_delete=models.CASCADE)

    sso_identity = models.CharField(default='', null=True, blank=True, max_length=255)
    sso_mail = LowercaseEmailField(default='', null=True, blank=True, validators=[validate_email])
    sso_department = models.CharField(default='', null=True, blank=True, max_length=255)

    sso_other_attributes = DateTimeAwareJSONField(default=dict, null=False, blank=True)

    class Meta:
        unique_together = ('user', 'institution')

    def __repr__(self):
        return f'<{self.__class__.__name__}(user={self.user._id}, institution={self.institution._id}, ' \
               f'identity={self.sso_identity}, mail={self.sso_mail}, department={self.sso_department}>'

    def __str__(self):
        return f'{self.user._id}::{self.institution._id}::{self.sso_identity}'


def get_user_by_institution_identity(institution, sso_identity):
    """Return the user with the given sso_identity for the given institution.
    """
    if not institution or not sso_identity:
        return None
    if sso_identity == InstitutionAffiliation.DEFAULT_VALUE_FOR_SSO_IDENTITY_NOT_AVAILABLE:
        return None
    try:
        affiliation = InstitutionAffiliation.objects.get(institution___id=institution._id, sso_identity=sso_identity)
    except InstitutionAffiliation.DoesNotExist:
        return None
    except InstitutionAffiliation.MultipleObjectsReturned:
        # TODO: add exception handling
        return None
    return affiliation.user
