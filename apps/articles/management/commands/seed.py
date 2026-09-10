"""
Seed the database with realistic IUBAT campus-newspaper data.

Usage::

    python manage.py seed                 # idempotent — safe to re-run
    python manage.py seed --reset         # wipe articles/comments/views first

Accounts created (password in parentheses):

    admin    / admin123     → Admin
    editor   / editor123    → Editor
    faculty  / faculty123   → Faculty Author (auto-publish)
    student  / student123   → Student Contributor (pending approval)
    reader   / reader123    → Reader
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.roles import CustomUserRole
from apps.articles.models import (
    Article,
    ArticleView,
    Category,
    Comment,
    Reaction,
    Tag,
)
from apps.newsletter.models import Subscriber

User = get_user_model()

CATEGORIES = [
    ("Campus News", "📰", 1, "Breaking and general news from across IUBAT."),
    ("Events", "🎉", 2, "Seminars, festivals, fairs and campus events."),
    ("Sports", "⚽", 3, "Inter-university matches, athletes and results."),
    ("Academic", "🎓", 4, "Research, exams, results and academic programs."),
    ("Clubs", "🎭", 5, "Student clubs, societies and volunteering."),
    ("Achievements", "🏆", 6, "Awards, competition wins and success stories."),
    ("Notice Board", "📢", 7, "Official university announcements."),
]

TAGS = [
    "admission", "seminar", "tech", "sports-week", "cse", "business",
    "culture", "research", "graduation", "blood-donation", "debate",
    "environment", "entrepreneurship", "scholarship", "workshop",
]

# (title, category_index, tag names, author_key, days_ago, featured, breaking)
ARTICLES = [
    ("IUBAT Celebrates Grand Foundation Day with Campus-Wide Festivities",
     0, ["culture"], "faculty", 1, True, False),
    ("Inter-University Football Championship Kicks Off at IUBAT Ground",
     2, ["sports-week"], "student", 2, True, True),
    ("CSE Department Launches New AI and Machine Learning Lab",
     3, ["tech", "cse"], "faculty", 3, True, False),
    ("Business Club Wins National Entrepreneurship Case Competition",
     5, ["entrepreneurship", "seminar"], "editor", 4, True, False),
    ("Spring Semester Admission Fair Draws Record Student Turnout",
     0, ["admission"], "faculty", 5, False, False),
    ("Cultural Night 2026: Music, Drama and Fashion Light Up the Campus",
     1, ["culture"], "student", 6, False, False),
    ("Debate Club Triumphs in Inter-University Parliamentary Debate",
     5, ["debate"], "editor", 7, False, False),
    ("Free Blood Donation Camp Organised by Volunteer Club",
     4, ["blood-donation"], "student", 8, False, False),
    ("Faculty Research on Climate-Smart Agriculture Published",
     3, ["research", "environment"], "faculty", 9, False, False),
    ("Workshop on Career Skills and Resume Building Held at IUBAT",
     1, ["workshop"], "faculty", 10, False, False),
    ("Table Tennis Team Brings Home Inter-University Runner-Up Trophy",
     2, ["sports-week"], "student", 11, False, False),
    ("Green Campus Drive: Students Plant 500 Saplings Around University",
     4, ["environment"], "student", 12, False, False),
    ("Merit Scholarships Awarded to 120 High-Achieving Students",
     5, ["scholarship"], "editor", 13, False, False),
    ("Important Notice: Midterm Examination Schedule Published",
     6, [], "admin", 5, False, False),
    ("Robotics Club Showcases Autonomous Rover at Tech Fair",
     4, ["tech", "workshop"], "student", 14, False, False),
    ("Alumni Entrepreneurs Share Startup Journeys at Business Summit",
     1, ["entrepreneurship", "seminar"], "faculty", 15, False, False),
]

PENDING_TITLES = [
    ("Students Petition for Extended Library Hours During Finals",
     0, ["library", "campus-life"]),
    ("New Indoor Basketball Court Expected by Next Semester",
     2, ["sports-week", "campus-life"]),
]


class Command(BaseCommand):
    help = "Seed realistic IUBAT Campus News data (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help="Delete existing articles, comments, views and reactions.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write("Resetting editorial data…")
            ArticleView.objects.all().delete()
            Reaction.objects.all().delete()
            Comment.objects.all().delete()
            Article.objects.all().delete()
            Tag.objects.all().delete()

        self.stdout.write(self.style.MIGRATE_HEADING("Seeding database…"))

        users = self._create_users()
        tags = self._create_tags()
        categories = self._create_categories()
        self._create_articles(users, tags, categories)
        self._create_subscribers()

        self.stdout.write(self.style.SUCCESS("✅ Seed complete!"))
        self.stdout.write(
            "\nLog in with one of these accounts:\n"
            "  admin   / admin123   (full control)\n"
            "  editor  / editor123  (approve/reject, dashboards)\n"
            "  faculty / faculty123 (auto-publish author)\n"
            "  student / student123 (contributor, pending approval)\n"
            "  reader  / reader123  (comments & reactions)\n"
        )

    # ------------------------------------------------------------------
    def _create_users(self):
        specs = [
            ("admin", "Admin", "User", CustomUserRole.ADMIN,
             "admin@iubatnews.edu", "admin123", True),
            ("editor", "Sadia", "Islam", CustomUserRole.EDITOR,
             "sadia.editor@iubatnews.edu", "editor123", True),
            ("faculty", "Dr. Rahim", "Chowdhury", CustomUserRole.FACULTY,
             "rahim.faculty@iubat.edu", "faculty123", True),
            ("student", "Tanvir", "Ahmed", CustomUserRole.STUDENT,
             "tanvir@iubat.edu", "student123", False),
            ("reader", "Nusrat", "Jahan", CustomUserRole.READER,
             "nusrat.reader@iubat.edu", "reader123", False),
        ]
        users = {}
        for uname, first, last, role, email, password, verified in specs:
            user, created = User.objects.get_or_create(
                username=uname,
                defaults={"email": email, "first_name": first,
                          "last_name": last},
            )
            user.role = role
            user.email = email
            user.first_name = first
            user.last_name = last
            user.is_verified = verified
            user.is_active = True
            user.bio = (
                f"{first} {last} writes for the IUBAT Campus News portal."
            )
            if role == CustomUserRole.ADMIN:
                user.is_staff = True
                user.is_superuser = True
            elif role == CustomUserRole.EDITOR:
                user.is_staff = True
            if created:
                user.set_password(password)
            else:
                user.set_password(password)  # reset seeded password
            if role == CustomUserRole.STUDENT:
                user.student_id = "021203" + str(len(uname)).zfill(2)
                user.department = "CSE"
                user.batch = 2022
            elif role == CustomUserRole.FACULTY:
                user.department = "CSE"
            user.save()
            users[uname] = user
        self.stdout.write(f"  ✓ {len(users)} users")
        return users

    def _create_tags(self):
        tags = {}
        for name in TAGS:
            tag, _ = Tag.objects.get_or_create(name=name)
            tags[name] = tag
        # Extra tags used by pending articles
        for extra in ("library", "campus-life"):
            tag, _ = Tag.objects.get_or_create(name=extra)
            tags[extra] = tag
        self.stdout.write(f"  ✓ {len(tags)} tags")
        return tags

    def _create_categories(self):
        cats = []
        for name, icon, order, desc in CATEGORIES:
            cat, _ = Category.objects.get_or_create(
                name=name,
                defaults={"icon": icon, "order": order, "description": desc},
            )
            cats.append(cat)
        self.stdout.write(f"  ✓ {len(cats)} categories")
        return cats

    def _article_body(self, title):
        return f"""
<p><strong>{title}.</strong> The IUBAT community came together this week as
students, faculty members and staff took part in one of the most anticipated
events of the academic calendar. Organisers said the turnout exceeded
expectations and reflected the growing enthusiasm across all departments.</p>

<h2>What happened</h2>
<p>Participants from the Computer Science and Engineering, Business
Administration, English and Agriculture programs joined the event. The day
began with an inaugural session addressed by senior faculty, followed by
student-led activities, exhibitions and panel discussions that continued
well into the afternoon.</p>

<blockquote>“This is exactly what campus life should feel like — students
leading, collaborating and learning together,” said a faculty coordinator.</blockquote>

<h2>Why it matters</h2>
<p>Beyond the celebration, the event highlighted the breadth of talent at
IUBAT. Several student teams presented projects and proposals developed
throughout the semester, with judges praising the quality and creativity of
the work.</p>

<ul>
  <li>Record participation from first-year students</li>
  <li>Cross-department collaboration on display</li>
  <li>New initiatives announced for the coming semester</li>
</ul>

<p>The editorial team will continue covering follow-up stories. Students and
club coordinators can send announcements and tips through the
<a href="/contact/">contact page</a>.</p>
"""

    def _create_articles(self, users, tags, categories):
        created_count = 0
        for title, cat_idx, tag_names, author_key, days_ago, feat, breaking \
                in ARTICLES:
            published = timezone.now() - timedelta(days=days_ago)
            article, created = Article.objects.get_or_create(
                title=title,
                defaults={
                    "author": users[author_key],
                    "category": categories[cat_idx],
                    "excerpt": title + " — full coverage, photos and "
                                      "student reactions from IUBAT campus.",
                    "content": self._article_body(title),
                    "status": Article.Status.PUBLISHED,
                    "is_featured": feat,
                    "is_breaking": breaking,
                    "published_at": published,
                    "submitted_at": published - timedelta(hours=2),
                    "views_count": 0,
                    "image_caption": "IUBAT campus coverage.",
                },
            )
            if created:
                article.tags.set([tags[t] for t in tag_names])
                self._fake_engagement(article, users,
                                      views=max(15, 200 - days_ago * 11),
                                      comments=2 if days_ago < 10 else 1)
                created_count += 1

        # Pending articles from the student contributor
        for title, cat_idx, tag_names in PENDING_TITLES:
            Article.objects.get_or_create(
                title=title,
                defaults={
                    "author": users["student"],
                    "category": categories[cat_idx],
                    "excerpt": "A student report awaiting editorial review: "
                               + title.lower(),
                    "content": self._article_body(title),
                    "status": Article.Status.PENDING,
                    "submitted_at": timezone.now() - timedelta(hours=5),
                },
            )

        # One rejected draft so the workflow UI has data
        Article.objects.get_or_create(
            title="Untitled Draft About Cafeteria Food Prices",
            defaults={
                "author": users["student"],
                "category": categories[0],
                "excerpt": "Investigation into recent price changes at the "
                           "campus cafeteria, needs more sources.",
                "content": "<p>Draft notes — needs interviews and data "
                           "before resubmission.</p>",
                "status": Article.Status.REJECTED,
                "rejection_reason": (
                    "Promising topic, but the report needs at least two "
                    "named interviews (students and cafeteria management) "
                    "and verifiable pricing data before publication."
                ),
                "reviewed_by": users["editor"],
            },
        )
        self.stdout.write(f"  ✓ {created_count} new published articles")

    def _fake_engagement(self, article, users, views, comments):
        # Views (analytical log) — triggers the view-counter signal.
        batch = [
            ArticleView(
                article=article,
                ip=f"103.10.{views % 250}.{(views * 7) % 250}",
                user_agent="Mozilla/5.0 (seed data)",
                timestamp=article.published_at
                + timedelta(hours=(i % 60)),
            )
            for i in range(views)
        ]
        ArticleView.objects.bulk_create(batch)
        # Set counter directly so it matches the batch even on re-runs.
        article.views_count = views

        # Reactions
        for i, (key, rtype) in enumerate(
            [("faculty", "like"), ("editor", "love"),
             ("student", "insightful"), ("reader", "like")]
        ):
            if views > i * 30:
                Reaction.objects.get_or_create(
                    article=article, user=users[key],
                    defaults={"reaction_type": rtype},
                )

        # Comments (approved)
        if comments:
            Comment.objects.get_or_create(
                article=article, user=users["reader"],
                body="Great coverage! Really enjoyed reading this. 📰",
                defaults={"is_approved": False},
            )
            Comment.objects.get_or_create(
                article=article, user=users["faculty"],
                body="Thanks to the editorial team for highlighting this.",
                defaults={"is_approved": True},
            )
        article.save(update_fields=["views_count"])

    def _create_subscribers(self):
        emails = [
            "student1@iubat.edu", "student2@iubat.edu",
            "faculty.member@iubat.edu", "news.fan@example.com",
        ]
        for email in emails:
            Subscriber.objects.get_or_create(email=email)
        self.stdout.write(f"  ✓ {len(emails)} newsletter subscribers")
