from django.conf import settings
from django.contrib.postgres.search import SearchVector
from django.core.management.base import BaseCommand, CommandError
from USCODE.models import Collection, Node


class Command(BaseCommand):
    help = 'Command to initialize project - USCODE'

    def _write_success(self, message: str):
        self.stdout.write(
            self.style.SUCCESS(message))

    def handle(self, *args, **options):
        try:
            # 1. Create needed USCODE
            usc_code, _ = Collection.objects.get_or_create(
                code=settings.USCODE)

            self._write_success("Success creating USCODE\n")

            # 2. Scrape all content for uscode
            usc_code: Collection = usc_code
            print("Started scraper")
            usc_code.start_scraper()

            # 3. Update vector_column
            vector = SearchVector('title', weight='A') + \
                SearchVector('content', weight='B')
            Node.objects.update(vector_column=vector)

        except Exception as e:
            import traceback
            traceback.print_exc()
            raise CommandError(e)
