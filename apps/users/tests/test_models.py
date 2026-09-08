from datetime import date, timedelta
import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test suite for the Custom User model."""

    def test_create_user_successful(self):
        """Test creating a regular user with valid phone and birthdate."""
        user = User.objects.create_user(
            phone="01012345678",
            password="SecurePassword123!",
            name="أحمد علي",
            birthday=date(1995, 5, 15),
        )
        assert user.phone == "01012345678"
        assert user.name == "أحمد علي"
        assert user.birthday == date(1995, 5, 15)
        assert user.role == User.Role.BUYER
        assert not user.is_active  # inactive by default until OTP verified
        assert not user.is_staff
        assert not user.is_superuser
        assert user.check_password("SecurePassword123!")

    def test_create_user_phone_normalization(self):
        """Test that phone number with country code gets normalized."""
        user = User.objects.create_user(
            phone="+201112345678",
            password="SecurePassword123!",
            name="محمد حسن",
            birthday=date(2000, 1, 1),
        )
        assert user.phone == "01112345678"

    def test_create_user_invalid_phone(self):
        """Test that invalid phone formats raise ValidationError."""
        with pytest.raises(ValidationError):
            User.objects.create_user(
                phone="0123456",  # too short
                password="SecurePassword123!",
                name="مستخدم جديد",
                birthday=date(1990, 1, 1),
            )

        with pytest.raises(ValidationError):
            User.objects.create_user(
                phone="07712345678",  # not a valid Egyptian mobile prefix
                password="SecurePassword123!",
                name="مستخدم جديد",
                birthday=date(1990, 1, 1),
            )

    def test_create_user_underage(self):
        """Test that users under 18 years of age cannot register."""
        underage_date = date.today() - timedelta(days=17 * 365)  # 17 years old
        with pytest.raises(ValidationError):
            User.objects.create_user(
                phone="01512345678",
                password="SecurePassword123!",
                name="قاصر",
                birthday=underage_date,
            )

    def test_create_superuser(self):
        """Test that create_superuser properly sets staff, superuser, and active flags."""
        admin_user = User.objects.create_superuser(
            phone="01212345678",
            password="AdminPassword123!",
            name="المدير",
            birthday=date(1985, 1, 1),
        )
        assert admin_user.phone == "01212345678"
        assert admin_user.is_active
        assert admin_user.is_staff
        assert admin_user.is_superuser
