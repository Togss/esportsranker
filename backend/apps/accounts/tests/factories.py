import factory
from django.contrib.auth.hashers import make_password
from apps.accounts.models import User, UserRole


class UserFactory(factory.django.DjangoModelFactory):
    """
    Base user factory. We'll subclass this for Admin, Moderator, Reviewer.
    """
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    password = make_password("testpass123")  # hashes it so DRF auth doesn't complain
    is_active = True
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    role = UserRole.REVIEWER  # default lowest-permission role

class AdminFactory(UserFactory):
    role = UserRole.ADMIN
    is_superuser = True
    is_staff = True


class ModeratorFactory(UserFactory):
    role = UserRole.MODERATOR
    is_superuser = False
    is_staff = True  # usually moderators can access some admin UI


class ReviewerFactory(UserFactory):
    role = UserRole.REVIEWER
    is_superuser = False
    is_staff = False