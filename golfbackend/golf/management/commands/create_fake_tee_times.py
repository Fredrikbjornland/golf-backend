from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from golf.models import GolfCourse, TeeTime


class Command(BaseCommand):
    help = "Creates fake tee times for testing purposes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Number of days to create tee times for (default: 7)",
        )
        parser.add_argument(
            "--courses",
            type=int,
            default=2,
            help="Number of courses to create tee times for (default: 2)",
        )

    def handle(self, *args, **options):
        days = options["days"]
        num_courses = options["courses"]

        courses = GolfCourse.objects.all()

        if not courses.exists():
            self.stdout.write(
                self.style.ERROR(
                    "No golf courses found. Please create some golf courses first."
                )
            )
            return

        # Create tee times for each course
        print(courses)
        for course in courses:
            self.stdout.write(f"Creating tee times for {course.name}...")

            # Create tee times for the next 'days' days
            for day in range(days):
                current_date = timezone.now() + timedelta(days=day)

                # Create tee times from 6:00 to 20:00 with 15-minute intervals
                for hour in range(6, 21):
                    for minute in [0, 15, 30, 45]:
                        time = current_date.replace(
                            hour=hour, minute=minute, second=0, microsecond=0
                        )

                        # Randomly determine availability
                        availability = random.choice(["Available", "Limited", "Full"])
                        available_spots = random.randint(0, 4)
                        expired = random.random() < 0.1  # 10% chance of being expired
                        price_in_ore = random.randint(
                            5000, 20000
                        )  # Random price between 50 and 200 NOK

                        TeeTime.objects.create(
                            time=time,
                            golf_course=course,
                            availability=availability,
                            available_spots=available_spots,
                            expired=expired,
                            price_in_ore=price_in_ore,
                        )

            self.stdout.write(
                self.style.SUCCESS(f"Successfully created tee times for {course.name}")
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created fake tee times for {num_courses} courses over {days} days"
            )
        )
