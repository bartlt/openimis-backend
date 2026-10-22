import random

from django.core.management.base import BaseCommand
from faker import Faker

from core.models import User
from insuree.models import Insuree
from policyholder.tests import create_test_policy_holder_user, create_test_policy_holder_insuree
from policyholder.tests.helpers_tests import create_test_policy_holder


class Command(BaseCommand):
    help = "This command will generate test PolicyHolders with some optional parameters. It is intended to simulate larger" \
           "databases for performance testing"
    insurees = None
    users = None

    USER_POLICYHOLDER = "user"
    INSUREE_POLICYHOLDER = "insuree"

    def add_arguments(self, parser):
        parser.add_argument("nb_policyholders", nargs=1, type=int)
        parser.add_argument("type", nargs=1, type=str, choices=[self.USER_POLICYHOLDER, self.INSUREE_POLICYHOLDER])
        parser.add_argument(
            '--verbose',
            action='store_true',
            dest='verbose',
            help='Be verbose about what it is doing',
        )
        parser.add_argument(
            '--locale',
            default="en",
            help="Used to adapt the fake names generation to the locale, using Faker, by default en",
        )

    def handle(self, *args, **options):
        fake = Faker(options["locale"])
        nb_policyholders = options["nb_policyholders"][0]
        ph_type = options["type"][0]
        verbose = options["verbose"]
        for policyholder_num in range(1, nb_policyholders + 1):
            props = dict(
                trade_name=fake.company(),
                address=fake.address(),
                phone=self.generate_phone_number(fake, 16),
                email=fake.email(),
            )
            policy_holder = create_test_policy_holder(custom_props=props)
            if ph_type == self.USER_POLICYHOLDER:
                user_pk = self.get_random_user_pk()
                user = User.objects.get(pk=user_pk)
                create_test_policy_holder_user(policy_holder=policy_holder, user=user)
            elif ph_type == self.INSUREE_POLICYHOLDER:
                insuree_pk = self.get_random_insuree_pk()
                insuree = Insuree.objects.get(pk=insuree_pk)
                create_test_policy_holder_insuree(policy_holder=policy_holder, insuree=insuree)
            if verbose:
                print(policyholder_num, "created policyholder", policy_holder.trade_name, policy_holder.pk)

    def generate_phone_number(self, fake, max_length):
        phone_number = fake.phone_number()
        if len(phone_number) > max_length:
            phone_number = phone_number[:max_length]
        return phone_number

    def get_random_user_pk(self):
        if not self.users:
            self.users = User.objects.filter(validity_to__isnull=True).values_list("pk", flat=True)
        return random.choice(self.users)

    def get_random_insuree_pk(self):
        if not self.insurees:
            self.insurees = Insuree.objects.filter(validity_to__isnull=True).values_list("pk", flat=True)
        return random.choice(self.insurees)
