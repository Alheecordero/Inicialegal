from django.core.management.base import BaseCommand

from apps.assistant.models import AssistantKnowledgeItem
from apps.assistant.services import clean_html
from apps.blog.models import Post
from apps.core.models import FAQ, Page, Plan, PracticeArea, Service


class Command(BaseCommand):
    help = "Sincroniza contenido publico del sitio para el asistente conversacional."

    def handle(self, *args, **options):
        seen = set()
        count = 0

        for item in self._iter_items():
            key = (item["source_type"], item["source_id"])
            seen.add(key)
            AssistantKnowledgeItem.objects.update_or_create(
                source_type=item["source_type"],
                source_id=item["source_id"],
                defaults={
                    "title": item["title"][:240],
                    "summary": item.get("summary", ""),
                    "content": item["content"],
                    "url": item.get("url", ""),
                    "source_updated_at": item.get("source_updated_at"),
                    "is_active": True,
                },
            )
            count += 1

        # Desactivar con precision los registros que ya no existen sin borrar historial admin.
        for item in AssistantKnowledgeItem.objects.filter(is_active=True):
            if (item.source_type, item.source_id) not in seen:
                item.is_active = False
                item.save(update_fields=["is_active", "updated_at"])

        self.stdout.write(self.style.SUCCESS(f"Contenido sincronizado para el asistente: {count} items."))

    def _iter_items(self):
        for faq in FAQ.objects.filter(is_active=True).select_related("plan"):
            title = faq.question
            plan = f"Plan relacionado: {faq.plan.name}. " if faq.plan_id else ""
            yield {
                "source_type": "faq",
                "source_id": faq.pk,
                "title": title,
                "summary": clean_html(faq.answer)[:280],
                "content": f"{title}\n{plan}{clean_html(faq.answer)}",
                "url": "/preguntas-frecuentes/",
                "source_updated_at": faq.updated_at,
            }

        for area in PracticeArea.objects.filter(is_active=True):
            yield {
                "source_type": "area",
                "source_id": area.pk,
                "title": area.name,
                "summary": area.short_description,
                "content": "\n".join(filter(None, [area.name, area.short_description, clean_html(area.description)])),
                "url": area.get_absolute_url(),
                "source_updated_at": area.updated_at,
            }

        for service in Service.objects.filter(is_active=True).select_related("area"):
            area = f"Area relacionada: {service.area.name}." if service.area_id else ""
            yield {
                "source_type": "service",
                "source_id": service.pk,
                "title": service.name,
                "summary": service.short_description,
                "content": "\n".join(
                    filter(None, [service.name, service.short_description, area, service.price_note, clean_html(service.description)])
                ),
                "url": service.get_absolute_url(),
                "source_updated_at": service.updated_at,
            }

        plans = Plan.objects.filter(is_active=True).prefetch_related("features", "benefits", "faqs")
        for plan in plans:
            features = "\n".join(f"- {f.title}: {f.text}" for f in plan.features.all())
            benefits = "\n".join(f"- {b.title}: {b.text}" for b in plan.benefits.all())
            faqs = "\n".join(f"- {f.question}: {f.answer}" for f in plan.faqs.filter(is_active=True))
            price = ""
            if plan.price_annual:
                price = f"Valor anual: {plan.currency} {plan.price_annual} {plan.price_suffix}. {plan.price_note}"
            yield {
                "source_type": "plan",
                "source_id": plan.pk,
                "title": plan.name,
                "summary": plan.summary,
                "content": "\n".join(
                    filter(
                        None,
                        [
                            plan.name,
                            plan.tagline,
                            plan.summary,
                            plan.problem_title,
                            plan.problem_text,
                            plan.solution_title,
                            plan.solution_text,
                            price,
                            clean_html(plan.description),
                            features,
                            benefits,
                            faqs,
                        ],
                    )
                ),
                "url": plan.get_absolute_url(),
                "source_updated_at": plan.updated_at,
            }

        for page in Page.objects.filter(is_published=True):
            yield {
                "source_type": "page",
                "source_id": page.pk,
                "title": page.title,
                "summary": page.meta_description or page.subtitle,
                "content": "\n".join(filter(None, [page.title, page.subtitle, clean_html(page.content)])),
                "url": page.get_absolute_url(),
                "source_updated_at": page.updated_at,
            }

        posts = Post.published.select_related("category").prefetch_related("areas", "tags")
        for post in posts:
            areas = ", ".join(area.name for area in post.areas.all())
            tags = ", ".join(tag.name for tag in post.tags.all())
            category = post.category.name if post.category_id else ""
            yield {
                "source_type": "post",
                "source_id": post.pk,
                "title": post.title,
                "summary": post.excerpt,
                "content": "\n".join(
                    filter(None, [post.title, post.excerpt, category, areas, tags, clean_html(post.content)])
                ),
                "url": post.get_absolute_url(),
                "source_updated_at": post.updated_at,
            }
