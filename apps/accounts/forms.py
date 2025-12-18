from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm


User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """
    自訂用戶註冊表單，綁定到 accounts.User 模型
    """

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class CustomUserChangeForm(UserChangeForm):
    """
    自訂用戶修改表單，綁定到 accounts.User 模型
    """

    class Meta(UserChangeForm.Meta):
        model = User
        fields = ("username", "email", "phone", "avatar", "bio")
