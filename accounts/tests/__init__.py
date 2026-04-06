import factory
from django.contrib.auth.models import User

from accounts.models import Profile


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "testpass123!")

    @factory.post_generation
    def ensure_profile(self, create, extracted, **kwargs):
        if create and not hasattr(self, "_profile_created"):
            try:
                self.profile
            except Profile.DoesNotExist:
                Profile.objects.create(user=self, display_name=self.username)
