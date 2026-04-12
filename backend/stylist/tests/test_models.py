from django.test import TestCase

from stylist.models import Occasion, Season, StyleTag, StylingRequest


class StylingRequestModelTests(TestCase):
    def test_can_create_styling_request(self):
        season = Season.objects.get(code="summer")
        occasion = Occasion.objects.get(code="office")
        style = StyleTag.objects.get(code="classic")

        request = StylingRequest.objects.create(
            season=season,
            occasion=occasion,
            style=style,
            additional_info="Keep it clean and simple.",
        )

        self.assertEqual(request.status, StylingRequest.Status.QUEUED)
        self.assertFalse(request.files_deleted)
