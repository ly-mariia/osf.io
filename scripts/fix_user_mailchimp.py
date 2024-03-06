from datetime import datetime
from logging import getLogger
import sys

from django.db import transaction
from pytz import UTC

from osf.models import OSFUser
from scripts import utils as script_utils
from website import settings
from website.app import setup_django
from website.mailchimp_utils import subscribe_mailchimp

setup_django()
logger = getLogger(__name__)


def main():
    dry = '--dry' in sys.argv
    if not dry:
        # If we're not running in dry mode log everything to a file
        script_utils.add_file_logger(logger, __file__)

    with transaction.atomic():
        start_time = datetime(2017, 12, 20, 8, 25, 25, tzinfo=UTC)
        end_time = datetime(2017, 12, 20, 18, 5, 1, tzinfo=UTC)

        users = OSFUser.objects.filter(is_registered=True, date_disabled__isnull=True, date_registered__range=[start_time, end_time])

        count = 0
        for user in users:
            if settings.MAILCHIMP_GENERAL_LIST not in user.mailchimp_mailing_lists:
                if not dry:
                    subscribe_mailchimp(settings.MAILCHIMP_GENERAL_LIST, user._id)
                    logger.info(f'User {user._id} has been subscribed to OSF general mailing list')
                count += 1

        logger.info(f'{count} users have been subscribed to OSF general mailing list')

        if dry:
            raise Exception('Abort Transaction - Dry Run')
    print('Done')

if __name__ == '__main__':
    main()
