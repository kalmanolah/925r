"""Feeds."""
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from django_ical.views import ICalFeed
from icalendar import vCalAddress
from django_ical.views import ICAL_EXTRA_FIELDS
from django_ical.feedgenerator import ITEM_EVENT_FIELD_MAP
from django_ical import feedgenerator
from ninetofiver import models


ICAL_EXTRA_FIELDS.append('status')
ITEM_EVENT_FIELD_MAP += (('status', 'status'),)
ITEM_EVENT_FIELD_MAP = [x for x in ITEM_EVENT_FIELD_MAP if x[0] != 'link']
feedgenerator.ITEM_EVENT_FIELD_MAP = ITEM_EVENT_FIELD_MAP


class BaseFeed(ICalFeed):
    """A base ICAL feed."""

    timezone = 'UTC'

    def item_guid(self, item):
        """Get item guid."""
        return '%s/%s/%s/%s' % ('925r', self.__class__.__name__, self.__class__.title.lower(), item.id)

    def item_link(self, item):
        """Get item link."""
        return ''


class LeaveFeed(BaseFeed):
    """A leave feed for all users."""

    product_id = '-//ninetofiver//LeaveFeed//EN'
    file_name = 'leave.ics'
    title = _('Leave')
    description = _('Leave')

    def items(self):
        """Get items."""
        return (models.LeaveDate.objects.all()
                .filter(Q(leave__status=models.STATUS_APPROVED) | Q(leave__status=models.STATUS_PENDING))
                .select_related('leave', 'leave__user', 'leave__leave_type')
                .order_by('-starts_at'))

    def item_title(self, item):
        """Get item title."""
        return str(item.leave)

    def item_description(self, item):
        """Get item description."""
        return None

    def item_start_datetime(self, item):
        """Get item start datetime."""
        return item.starts_at

    def item_end_datetime(self, item):
        """Get item end datetime."""
        return item.ends_at

    def item_created(self, item):
        """Get item created."""
        return item.leave.created_at

    def item_updateddate(self, item):
        """Get item updateddate."""
        return item.leave.updated_at

    def item_organizer(self, item):
        """Get item organizer."""
        organizer = item.leave.user.email
        organizer = vCalAddress(organizer)
        organizer.params["CN"] = str(item.leave.user)

        return organizer

    def item_status(self, item):
        """Get item status."""
        status = item.leave.status

        if status == models.STATUS_PENDING:
            status = 'TENTATIVE'
        elif status == models.STATUS_APPROVED:
            status = 'CONFIRMED'
        elif status == models.STATUS_REJECTED:
            status = 'CANCELLED'

        return status


class UserLeaveFeed(LeaveFeed):
    """A leave feed for a specific user."""

    def get_object(self, request, user, **kwargs):
        """Get object."""
        return user

    def items(self, obj):
        """Get items."""
        return super().items().filter(leave__user=obj)


class WhereaboutFeed(BaseFeed):
    """A whereabout feed for all users."""

    product_id = '-//ninetofiver//WhereaboutFeed//EN'
    file_name = 'whereabouts.ics'
    title = _('Whereabouts')
    description = _('Whereabouts')

    def items(self):
        """Get items."""
        return (models.Whereabout.objects.all()
                .select_related('timesheet', 'timesheet__user', 'location')
                .order_by('-starts_at'))

    def item_title(self, item):
        """Get item title."""
        return str(item)

    def item_description(self, item):
        """Get item description."""
        return None

    def item_start_datetime(self, item):
        """Get item start datetime."""
        return item.starts_at

    def item_end_datetime(self, item):
        """Get item end datetime."""
        return item.ends_at

    def item_created(self, item):
        """Get item created."""
        return item.created_at

    def item_updateddate(self, item):
        """Get item updateddate."""
        return item.updated_at

    def item_organizer(self, item):
        """Get item organizer."""
        organizer = item.timesheet.user.email
        organizer = vCalAddress(organizer)
        organizer.params["CN"] = str(item.timesheet.user)

        return organizer

    def item_status(self, item):
        """Get item status."""
        status = 'CONFIRMED'

        return status


class UserWhereaboutFeed(WhereaboutFeed):
    """A whereabout feed for a specific user."""

    def get_object(self, request, user, **kwargs):
        """Get object."""
        return user

    def items(self, obj):
        """Get items."""
        return super().items().filter(timesheet__user=obj)
