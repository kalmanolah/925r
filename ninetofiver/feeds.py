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


class LeaveFeed(ICalFeed):
    """A leave feed."""

    product_id = '-//ninetofiver//LeaveFeed//EN'
    timezone = 'UTC'
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
        return str(item.leave.description)

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

    def item_guid(self, item):
        """Get item guid."""
        return '%s/%s/%s/%s' % ('925r', self.__class__.__name__, self.__class__.title.lower(), item.id)

    def item_link(self, item):
        """Get item link."""
        return ''

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
