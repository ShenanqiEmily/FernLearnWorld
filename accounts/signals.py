from .utils import (
    generate_student_credentials,
    generate_lecturer_credentials,
    send_new_account_email,
)


def display_name_from_social_extra_data(provider, extra_data):
    """
    Best-effort real display name from a django-allauth SocialAccount's
    extra_data, keyed by provider.

    Google and Facebook's allauth adapters already map their profile data
    onto User.first_name/last_name correctly (given_name/family_name for
    Google, first_name/last_name for Facebook), so user.first_name is
    already populated by the time our signal runs for those two — this is
    only actually needed for LINE, whose allauth provider (as of 65.1.0)
    reads extra_data["name"]/["first_name"] which LINE's API never sends
    (LINE only sends "displayName"), so it silently comes back empty and
    the user's LINE user ID (used as username, for uniqueness) ends up
    showing everywhere get_full_name() falls back to username. Kept
    provider-generic (not just "if line") in case that allauth bug gets
    fixed differently later, or a future provider has the same gap.
    """
    extra_data = extra_data or {}
    if provider == "line":
        return extra_data.get("displayName")
    if provider == "google":
        return extra_data.get("name") or extra_data.get("given_name")
    if provider == "facebook":
        return extra_data.get("name")
    return extra_data.get("name") or extra_data.get("displayName")


def social_login_creates_student(sender, request, user, sociallogin=None, **kwargs):
    """
    First-time social login (Google/Facebook/LINE via django-allauth) has
    no equivalent of the public register form's StudentAddForm.save() to
    create the matching Student row — do the same minimal setup here so a
    social user ends up in the exact same state as a self-registered one
    (is_student=True, a Student row with level/program left blank).
    """
    from .models import Student
    from subscriptions.models import Subscription

    user.is_active = True
    user.is_student = True
    user.is_lecturer = False
    user.is_parent = False

    # Only fill in a name if allauth didn't already set one (see
    # display_name_from_social_extra_data's docstring) — never overwrite
    # a real first_name that's already correct.
    if not user.first_name and sociallogin is not None:
        display_name = display_name_from_social_extra_data(
            sociallogin.account.provider, sociallogin.account.extra_data
        )
        if display_name:
            user.first_name = display_name

    user.save()

    Student.objects.get_or_create(student=user)

    if not Subscription.objects.filter(user=user).exists():
        Subscription.objects.create(user=user, tier="free", status="active")


def post_save_account_receiver(sender, instance=None, created=False, *args, **kwargs):
    """
    Send email notification
    """
    if created:
        if instance.is_student:
            # username, password = generate_student_credentials()
            # instance.username = username
            # instance.set_password(password)
            instance.save()
            # Send email with the generated credentials
            # send_new_account_email(instance, password)

        if instance.is_lecturer:
            username, password = generate_lecturer_credentials()
            instance.username = username
            instance.set_password(password)
            instance.save()
            # Send email with the generated credentials
            send_new_account_email(instance, password)
