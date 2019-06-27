from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import OuterRef, Q, Subquery
from django.utils.functional import cached_property
from django.utils.timezone import now, utc
from django.utils.translation import ugettext_lazy as _

from resources.models import Reservation, Resource
from resources.models.utils import generate_id

from .exceptions import OrderStateTransitionError
from .utils import round_price

# The best way for representing non existing archived_at would be using None for it,
# but that would not work with the unique_together constraint, which brings many
# benefits, so we use this sentinel value instead of None.
ARCHIVED_AT_NONE = datetime(9999, 12, 31, tzinfo=utc)

TAX_PERCENTAGES = [Decimal(x) for x in (
    '0.00',
    '10.00',
    '14.00',
    '24.00',
)]

DEFAULT_TAX_PERCENTAGE = Decimal('24.00')


class ProductQuerySet(models.QuerySet):
    def current(self):
        return self.filter(archived_at=ARCHIVED_AT_NONE)

    def rents(self):
        return self.filter(type=Product.RENT)


class Product(models.Model):
    RENT = 'rent'
    TYPE_CHOICES = (
        (RENT, _('rent')),
    )

    PRICE_PER_HOUR = 'per_hour'
    PRICE_FIXED = 'fixed'
    PRICE_TYPE_CHOICES = (
        (PRICE_PER_HOUR, _('per hour')),
        (PRICE_FIXED, _('fixed')),
    )

    created_at = models.DateTimeField(verbose_name=_('created at'), auto_now_add=True)

    # This ID is common to all versions of the same product, and is the one
    # used as ID in the API.
    product_id = models.CharField(max_length=100, verbose_name=_('product ID'), editable=False, db_index=True)

    # archived_at determines when this version of the product has been either (soft)
    # deleted or replaced by a newer version. Value ARCHIVED_AT_NONE means this is the
    # current version in use.
    archived_at = models.DateTimeField(
        verbose_name=_('archived_at'), db_index=True, editable=False, default=ARCHIVED_AT_NONE
    )

    type = models.CharField(max_length=32, verbose_name=_('type'), choices=TYPE_CHOICES, default=RENT)
    sku = models.CharField(max_length=255, verbose_name=_('SKU'))
    name = models.CharField(max_length=100, verbose_name=_('name'), blank=True)
    description = models.TextField(verbose_name=_('description'), blank=True)

    pretax_price = models.DecimalField(
        verbose_name=_('pretax price'), max_digits=19, decimal_places=10, validators=[MinValueValidator(0)]
    )
    tax_percentage = models.DecimalField(
        verbose_name=_('tax percentage'), max_digits=5, decimal_places=2, default=DEFAULT_TAX_PERCENTAGE,
        choices=[(tax, str(tax)) for tax in TAX_PERCENTAGES]
    )
    price_type = models.CharField(
        max_length=32, verbose_name=_('price type'), choices=PRICE_TYPE_CHOICES, default=PRICE_PER_HOUR
    )

    resources = models.ManyToManyField(Resource, verbose_name=_('resource'), related_name='products', blank=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')
        ordering = ('id',)
        unique_together = ('archived_at', 'product_id')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.id:
            resources = self.resources.all()
            Product.objects.filter(id=self.id).update(archived_at=now())
            self.id = None
        else:
            resources = []
            self.product_id = generate_id()

        super().save(*args, **kwargs)

        if resources:
            self.resources.set(resources)

    def delete(self, *args, **kwargs):
        Product.objects.filter(id=self.id).update(archived_at=now())

    def get_price(self):
        return round_price(self.pretax_price * (1 + Decimal(self.tax_percentage) / 100))

    def get_pretax_price_for_time_range(self, begin: datetime, end: datetime, rounded: bool = True) -> Decimal:
        assert begin < end

        if self.price_type == Product.PRICE_PER_HOUR:
            price = self.pretax_price * Decimal((end - begin) / timedelta(hours=1))
        elif self.price_type == Product.PRICE_FIXED:
            price = self.pretax_price
        else:
            raise NotImplementedError('Cannot calculate price, unknown price type "{}".'.format(self.price_type))

        if rounded:
            price = round_price(price)

        return price

    def get_price_for_time_range(self, begin: datetime, end: datetime, rounded: bool = True) -> Decimal:
        pretax_price = self.get_pretax_price_for_time_range(begin, end, rounded=False)
        price = pretax_price * (1 + Decimal(self.tax_percentage) / 100)

        if rounded:
            price = round_price(price)

        return price

    def get_pretax_price_for_reservation(self, reservation: Reservation, rounded: bool = True) -> Decimal:
        return self.get_pretax_price_for_time_range(reservation.begin, reservation.end, rounded)

    def get_price_for_reservation(self, reservation: Reservation, rounded: bool = True) -> Decimal:
        return self.get_price_for_time_range(reservation.begin, reservation.end, rounded)


class OrderQuerySet(models.QuerySet):
    def can_view(self, user):
        if not user.is_authenticated:
            return self.none()

        allowed_resources = Resource.objects.with_perm('can_view_reservation_product_orders', user)
        allowed_reservations = Reservation.objects.filter(Q(resource__in=allowed_resources) | Q(user=user))

        return self.filter(reservation__in=allowed_reservations)


class Order(models.Model):
    WAITING = 'waiting'
    CONFIRMED = 'confirmed'
    REJECTED = 'rejected'
    EXPIRED = 'expired'
    CANCELLED = 'cancelled'

    STATE_CHOICES = (
        (WAITING, _('waiting')),
        (CONFIRMED, _('confirmed')),
        (REJECTED, _('rejected')),
        (EXPIRED, _('expired')),
        (CANCELLED, _('cancelled')),
    )

    state = models.CharField(max_length=32, verbose_name=_('state'), choices=STATE_CHOICES, default=WAITING)
    order_number = models.CharField(max_length=64, verbose_name=_('order number'), unique=True, default=generate_id)
    reservation = models.ForeignKey(
        Reservation, verbose_name=_('reservation'), related_name='orders', on_delete=models.PROTECT
    )

    payer_first_name = models.CharField(max_length=100, verbose_name=_('payer first name'))
    payer_last_name = models.CharField(max_length=100, verbose_name=_('payer last name'))
    payer_email_address = models.EmailField(verbose_name=_('payer email address'))
    payer_address_street = models.CharField(max_length=255, verbose_name=_('payer address street'))
    payer_address_zip = models.CharField(max_length=16, verbose_name=_('payer address zip'))
    payer_address_city = models.CharField(max_length=100, verbose_name=_('payer address city'))

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = _('order')
        verbose_name_plural = _('orders')
        ordering = ('id',)

    def __str__(self):
        return '{} {}'.format(self.order_number, self.reservation)

    @cached_property
    def created_at(self):
        first_log_entry = self.log_entries.first()
        return first_log_entry.timestamp if first_log_entry else None

    @classmethod
    def update_expired_orders(cls) -> int:
        earliest_allowed_timestamp = now() - timedelta(minutes=settings.RESPA_PAYMENTS_PAYMENT_WAITING_TIME)
        log_entry_timestamps = OrderLogEntry.objects.filter(order=OuterRef('pk')).order_by('id').values('timestamp')
        too_old_waiting_orders = cls.objects.filter(
            state=cls.WAITING
        ).annotate(
            created_at=Subquery(
                log_entry_timestamps[:1]
            )
        ).filter(
            created_at__lt=earliest_allowed_timestamp
        )
        for order in too_old_waiting_orders:
            order.set_state(cls.EXPIRED)

        return too_old_waiting_orders.count()

    def save(self, *args, **kwargs):
        is_new = not bool(self.id)
        super().save(*args, **kwargs)

        if is_new:
            self.create_log_entry(state_change=self.state)

    def get_pretax_price(self) -> Decimal:
        return sum(order_line.get_pretax_price() for order_line in self.order_lines.all())

    def get_price(self) -> Decimal:
        return sum(order_line.get_price() for order_line in self.order_lines.all())

    def set_state(self, new_state: str, log_message: str = None, save: bool = True) -> None:
        assert new_state in (Order.WAITING, Order.CONFIRMED, Order.REJECTED, Order.EXPIRED, Order.CANCELLED)

        old_state = self.state
        if new_state == old_state:
            return

        if old_state != Order.WAITING:
            raise OrderStateTransitionError('Cannot set order {} state, it is in an invalid state "{}".',
                                            self.order_number, old_state)

        self.state = new_state

        if new_state == Order.CONFIRMED:
            self.reservation.set_state(Reservation.CONFIRMED, self.reservation.user)
        elif new_state in (Order.REJECTED, Order.EXPIRED, Order.CANCELLED):
            self.reservation.set_state(Reservation.CANCELLED, self.reservation.user)

        if save:
            self.save()

        self.create_log_entry(state_change=new_state, message=log_message)

    def create_log_entry(self, message: str = None, state_change: str = None) -> None:
        OrderLogEntry.objects.create(order=self, state_change=state_change or '', message=message or '')


class OrderLine(models.Model):
    order = models.ForeignKey(Order, verbose_name=_('order'), related_name='order_lines', on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, verbose_name=_('product'), related_name='order_lines', on_delete=models.PROTECT
    )

    quantity = models.PositiveIntegerField(verbose_name=_('quantity'), default=1)

    class Meta:
        verbose_name = _('order line')
        verbose_name_plural = _('order lines')
        ordering = ('id',)

    def __str__(self):
        return str(self.product)

    def get_pretax_price(self) -> Decimal:
        return self.product.get_pretax_price_for_reservation(self.order.reservation) * self.quantity

    def get_price(self) -> Decimal:
        return self.product.get_price_for_reservation(self.order.reservation) * self.quantity


class OrderLogEntry(models.Model):
    order = models.ForeignKey(
        Order, verbose_name=_('order log entry'), related_name='log_entries', on_delete=models.CASCADE
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    state_change = models.CharField(
        max_length=32, verbose_name=_('state change'), choices=Order.STATE_CHOICES, blank=True
    )
    message = models.TextField(blank=True)

    class Meta:
        verbose_name = _('order log entry')
        verbose_name_plural = _('order log entries')
        ordering = ('id',)

    def __str__(self):
        return '{} order {} state change {} message {}'.format(
            self.timestamp, self.order_id, self.state_change or None, self.message or None
        )