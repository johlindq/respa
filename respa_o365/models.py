from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

class OutlookTokenRequestData(models.Model):
    state = models.TextField(unique=True)
    created_at = models.DateTimeField()
    return_to = models.URLField()
    resource = models.ForeignKey('resources.Resource', verbose_name=_('Resource'),
                                    blank=False, null=False, on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', verbose_name=_('User'), null=False,
                             blank=False, db_index=True, on_delete=models.CASCADE)

class OutlookCalendarLink(models.Model):
    resource = models.ForeignKey('resources.Resource', verbose_name=_('Resource'),
                                    blank=False, null=False, on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', verbose_name=_('User'), null=False,
                             blank=False, db_index=True, on_delete=models.CASCADE)
    token = models.TextField(verbose_name=_('Token'))
    reservation_calendar_id = models.TextField(verbose_name=_('Outlook calendar id'))
    availability_calendar_id = models.TextField(verbose_name=_('Availability calendar id'))
    respa_reservation_sync_memento = models.TextField(verbose_name=_('Last known state of Respa reservations'), null=True)
    exchange_reservation_sync_memento = models.TextField(verbose_name=_('Last known state of Exchange reservations'), null=True)
    respa_availability_sync_memento = models.TextField(verbose_name=_('Last known state of Respa availability'), null=True)
    exchange_availability_sync_memento = models.TextField(verbose_name=_('Last known state of Exchange availability'), null=True)
    exchange_subscription_id = models.TextField(verbose_name=_('Id of the registered notification listener'), null=True)
    exchange_subscription_secret = models.TextField(verbose_name=_('Secret used by the notifier'), null=True)

class OutlookCalendarReservation(models.Model):
    calendar_link = models.ForeignKey('OutlookCalendarLink', verbose_name=_('Calendar Link'),
                        blank=False, null=False, on_delete=models.CASCADE)
    reservation = models.ForeignKey('resources.Reservation', verbose_name=_('Reservation'),
                                    blank=False, null=False, on_delete=models.CASCADE)
    exchange_id = models.TextField(verbose_name=_('Exchange ID'), unique=True)
    exchange_change_key = models.TextField(verbose_name=_('Exchange Change Key'))
    respa_change_key = models.TextField(verbose_name=_('Respa Change Key'))

class OutlookCalendarAvailability(models.Model):
    calendar_link = models.ForeignKey('OutlookCalendarLink', verbose_name=_('Calendar Link'),
                    blank=False, null=False, on_delete=models.CASCADE)
    period = models.ForeignKey('resources.Period', verbose_name=_('Period'),
                                    blank=False, null=False, on_delete=models.CASCADE)
    exchange_id = models.TextField(verbose_name=_('Exchange ID'), unique=True)
    exchange_change_key = models.TextField(verbose_name=_('Exchange Change Key'))
    respa_change_key = models.TextField(verbose_name=_('Respa Change Key'))
