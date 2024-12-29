import rules
from authentication.models import CustomUser
from .choices import EventStatusChoices


@rules.predicate(bind=True)
def user_can_book_event(self, user: CustomUser, event, *args, **kwargs):
    if not user.role == CustomUser.UserRoleChoices.PARENT:
        return False
    if self.context.args:
        if not event.status == EventStatusChoices.UNOCCUPIED:
            return False
        return event.check_parent_can_book_event(user)
    return False


@rules.predicate(bind=True)
def is_event_owner(self, user, event, *args, **kwargs):
    if not user.role == CustomUser.UserRoleChoices.TEACHER:
        return False
    if self.context.args:
        return event.teacher == user
    return False


@rules.predicate(bind=True)
def is_event_participant(self, user, event, *args, **kwargs):
    if not user.role == CustomUser.UserRoleChoices.PARENT:
        return False
    if event.status == EventStatusChoices.UNOCCUPIED:
        return False
    if event.status == EventStatusChoices.CANCELED:
        return False
    if self.context.args:
        return event.parent == user
    return False


can_edit_event = is_event_owner | is_event_participant
