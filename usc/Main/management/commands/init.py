from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from CFR.models import CFRNode


class Command(BaseCommand):
    help = 'Command to initialize project - CFR'

    def _write_success(self, message: str):
        self.stdout.write(
            self.style.SUCCESS(message))

    def handle(self, *args, **options):
        try:
            titles = CFRNode.objects.get_titles()

            for title in titles:
                with transaction.atomic():
                    title.get_child_nodes()
                    self._write_success(f"Title {title} created")

        except Exception as e:
            import traceback
            traceback.print_exc()
            raise CommandError(e)
