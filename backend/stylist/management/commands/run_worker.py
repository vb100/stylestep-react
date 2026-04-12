from __future__ import annotations

import time
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from stylist.tasks import cleanup_old_media_files, process_next_styling_request


class Command(BaseCommand):
    help = "Run the React-version styling worker without Celery."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Process at most one queued request and exit.",
        )
        parser.add_argument(
            "--poll-interval",
            type=float,
            default=settings.WORKER_POLL_INTERVAL_SECONDS,
            help="Seconds to sleep between polling attempts when the queue is empty.",
        )
        parser.add_argument(
            "--cleanup-interval-hours",
            type=int,
            default=settings.WORKER_CLEANUP_INTERVAL_HOURS,
            help="How often to run media cleanup while the worker is running.",
        )
        parser.add_argument(
            "--skip-cleanup",
            action="store_true",
            help="Disable periodic media cleanup checks in the worker loop.",
        )

    def handle(self, *args, **options):
        poll_interval = max(float(options["poll_interval"]), 0.5)
        once = bool(options["once"])
        skip_cleanup = bool(options["skip_cleanup"])
        cleanup_interval = timedelta(hours=max(int(options["cleanup_interval_hours"]), 1))
        next_cleanup_at = timezone.now()

        self.stdout.write(self.style.SUCCESS("Styling worker started."))

        while True:
            now = timezone.now()
            if not skip_cleanup and now >= next_cleanup_at:
                cleaned_records = cleanup_old_media_files(settings.MEDIA_CLEANUP_DAYS)
                self.stdout.write(f"Cleanup finished. Cleaned records: {cleaned_records}")
                next_cleanup_at = now + cleanup_interval

            styling_request = process_next_styling_request()

            if once:
                if styling_request:
                    self.stdout.write(f"Processed request {styling_request.id}")
                else:
                    self.stdout.write("No queued requests found.")
                break

            if styling_request is None:
                time.sleep(poll_interval)
