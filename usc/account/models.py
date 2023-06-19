from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.urls import reverse
from utils.general import send_email
from utils.validators import validate_phone, validate_special_char
from django.dispatch import receiver
from django.db.models.signals import post_save


class UserManager(BaseUserManager):
    def create_user(
        self, email, password=None, is_active=True,
        is_staff=False, is_admin=False, normal=False, seller=False
    ):
        if not email:
            raise ValueError("User must provide an email")

        user: User = self.model(
            email=self.normalize_email(email)
        )
        user.set_password(password)
        user.active = is_active
        user.admin = is_admin
        user.staff = is_staff
        user.save(using=self._db)

        return user

    def create_staff(self, email, password=None):
        user = self.create_user(
            email=email, is_active=True, password=password, is_staff=True)
        return user

    def create_superuser(self, email, password=None):
        user = self.create_user(
            email=email, is_active=True,
            password=password, is_staff=True,
            is_admin=True
        )
        return user


class User(AbstractBaseUser):
    email = models.EmailField(unique=True)

    # Admin fields
    active = models.BooleanField(default=True)
    staff = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now=True)
    verified_email = models.BooleanField(default=False)

    REQUIRED_FIELDS = []
    USERNAME_FIELD = "email"

    objects = UserManager()

    def account_type(self):
        if self.is_admin:
            return 'Admin'
        elif self.is_staff:
            return 'Staff'
        return 'User'

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    def __str__(self):
        return self.email

    def email_user(self, subject, message, fail=True):
        return send_email(self.email, subject, message, fail)

    @property
    def is_active(self):
        return self.active

    @property
    def is_staff(self):
        return self.staff

    @property
    def is_admin(self):
        return self.admin


def profile_photo_upload(instance, filename):
    """
    Upload profile photo to MEDIA_ROOT/profile/<user_id>/photo.<ext>
    """
    return f"profile/{instance.user.id}/photo.{filename.split('.')[-1]}"


class Profile(models.Model):
    GENDER = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    first_name = models.CharField(
        max_length=60, validators=[validate_special_char])
    last_name = models.CharField(
        max_length=60, validators=[validate_special_char])
    phone = models.CharField(max_length=16, validators=[validate_phone])

    city = models.CharField(max_length=50, help_text="City/Town")
    state = models.CharField(max_length=50, help_text="State/Province")
    country = models.CharField(max_length=50, help_text="Residence Country")

    gender = models.CharField(max_length=10, choices=GENDER)
    photo = models.ImageField(
        null=True, blank=True,
        upload_to=profile_photo_upload,
        help_text="Profile Photo"
    )

    __photo = None

    @property
    def get_fullname(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self) -> str:
        return self.get_fullname

    def get_absolute_url(self):
        return reverse('dashboard:account_update', kwargs={'id': self.id})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__photo = self.photo

    def save(self, *args, **kwargs):
        if self.photo != self.__photo:
            self.__photo.delete()
            self.__photo = self.photo
        super().save(*args, **kwargs)


class UsedResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.user.profile.get_fullname


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
