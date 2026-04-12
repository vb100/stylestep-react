from django.conf import settings
from django.core.management.base import BaseCommand

from stylist.services import cleanup_old_requests_media


class Command(BaseCommand):
    help = "Delete old uploaded media files and mark request records as files_deleted."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=settings.MEDIA_CLEANUP_DAYS,
            help=f"Delete files older than this many days (default: {settings.MEDIA_CLEANUP_DAYS}).",
        )

    def handle(self, *args, **options):
        days = options["days"]
        cleaned_count = cleanup_old_requests_media(days=days)
        self.stdout.write(self.style.SUCCESS(f"Cleanup completed. Updated records: {cleaned_count}"))
