from django.db import models
from django.utils.translation import gettext_lazy as _
from garpix_utils.string import get_random_string
from django.db.models import Q

from garpix_keycloak.models import KeycloakGroup

class KeycloakUserMixin(models.Model):
    keycloak_id = models.CharField(max_length=128, null=True, blank=True, verbose_name=_('Keycloak ID'))

    keycloak_groups = models.ManyToManyField(
        KeycloakGroup,
        verbose_name=_('keycloak groups'),
        blank=True,
        help_text=_(
            'The keycloak groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="user_set",
        related_query_name="user",
    )

    class Meta:
        abstract = True

    @classmethod
    def create_keycloak_user(cls, keycloak_data):
        email = keycloak_data.get('email')
        username = keycloak_data.get('preferred_username')
        keycloak_id = keycloak_data.get('sub')

        existing_user = cls.objects.filter(
            Q(email=email, username=username) | Q(email__isnull=True, username=username)
        ).first()

        if existing_user:
            existing_user.keycloak_id = keycloak_id
            existing_user.save()
            return existing_user

        if email:
            conflicting_email_user = cls.objects.filter(email=email).exclude(username=username).first()
            if conflicting_email_user:
                raise ValueError(f"A user with email {email} already exists.")

        if username:
            conflicting_username_user = cls.objects.filter(username=username).exclude(email=email).first()
            if conflicting_username_user:
                raise ValueError(f"A user with username {username} already exists.")

        user = cls.objects.create_user(
            keycloak_id=keycloak_id,
            first_name=keycloak_data.get('given_name', ''),
            last_name=keycloak_data.get('family_name', ''),
            username=username,
            password=get_random_string(25),
            email=email
        )

        return user
