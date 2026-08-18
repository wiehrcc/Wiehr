import logging
from itertools import islice
from typing import Iterable, Optional

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def _get_from_email() -> str:
    if getattr(settings, "DEFAULT_FROM_EMAIL", None):
        return settings.DEFAULT_FROM_EMAIL
    if getattr(settings, "EMAIL_HOST_USER", None):
        return settings.EMAIL_HOST_USER
    raise ImproperlyConfigured(
        "DEFAULT_FROM_EMAIL or EMAIL_HOST_USER must be configured to send emails."
    )


def _chunked(iterable: Iterable[str], size: int):
    iterator = iter(iterable)
    while True:
        chunk = list(islice(iterator, size))
        if not chunk:
            return
        yield chunk


def _render_email(template_name: str, context: dict) -> tuple[str, str]:
    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)
    return text_content, html_content


def _build_default_context(extra: Optional[dict] = None) -> dict:
    base_context = {
        "site_url": getattr(settings, "SITE_URL", ""),
        "site_url_nodashed": getattr(settings, "SITE_URL_NODASHED", ""),
        "media_full": getattr(settings, "MEDIA_FULL", ""),
        "logo_url": f"{getattr(settings, 'SITE_URL_NODASHED', '')}{settings.STATIC_URL}img/seo/network.png",
    }
    if extra:
        base_context.update(extra)
    return base_context


def send_templated_email(subject: str, recipients: Iterable[str], template_name: str, context: Optional[dict] = None, personalize: bool = False, recipient_context_func: Optional[callable] = None) -> int:
    to_send = list({email.strip().lower() for email in recipients if email})
    if not to_send:
        logger.info("No recipients found for subject '%s'", subject)
        return 0

    from_email = _get_from_email()
    base_context = _build_default_context(context or {})

    sent_count = 0
    batch_size = int(getattr(settings, "TEAM_EMAIL_BATCH_SIZE", 50))

    if personalize and recipient_context_func:
        for email in to_send:
            personal_context = base_context.copy()
            if recipient_context_func:
                personal_context.update(recipient_context_func(email))
            
            text_content, html_content = _render_email(template_name, personal_context)
            message = EmailMultiAlternatives(subject=subject, body=text_content, from_email=from_email, to=[email])
            message.attach_alternative(html_content, "text/html")
            message.send(fail_silently=False)
            sent_count += 1
            logger.debug("Sent personalized email '%s' to %s", subject, email)
    else:
        text_content, html_content = _render_email(template_name, base_context)

        for chunk in _chunked(to_send, batch_size):
            message = EmailMultiAlternatives(subject=subject, body=text_content, from_email=from_email, to=[], bcc=chunk)
            message.attach_alternative(html_content, "text/html")
            message.send(fail_silently=False)
            sent_count += len(chunk)
            logger.debug("Sent email '%s' to batch of %s recipients", subject, len(chunk))

    logger.info("Email '%s' sent to %s recipient(s)", subject, sent_count)
    return sent_count


def send_team_campaign(subject: str, body: str, *, title: Optional[str] = None, button_text: Optional[str] = None, button_url: Optional[str] = None, extra_context: Optional[dict] = None, queryset=None) -> int:
    from .models import Team

    if queryset is None:
        queryset = Team.objects.filter(is_blacklist=False, is_disconnected=False)

    recipients = queryset.values_list("email", flat=True)
    
    def recipient_context_func(email):
        try:
            team = Team.objects.get(email=email)
            return {"disconnect_token": team.disconnect_token, "recipient_email": email}
        except Team.DoesNotExist:
            return {"disconnect_token": None, "recipient_email": email}
    
    context = {
        "title": title,
        "headline": title or subject,
        "body": body,
        "button_text": button_text,
        "button_url": button_url,
    }
    if extra_context:
        context.update(extra_context)

    return send_templated_email(subject, recipients, "emails/team_campaign.html", context, personalize=True, recipient_context_func=recipient_context_func)


def send_license_email(licence) -> bool:
    from .license_builder import build_agreement_pdf

    from_email = _get_from_email()
    subject = f"Your {licence.license_type.name} — {licence.get_product_display()}"
    context = _build_default_context({
        "licence": licence,
    })
    text_content, html_content = _render_email("emails/license_issued.html", context)

    message = EmailMultiAlternatives(subject=subject, body=text_content, from_email=from_email, to=[licence.licensee_email])
    message.attach_alternative(html_content, "text/html")
    message.attach(f"{licence.internal_id}-license.pdf", build_agreement_pdf(licence), "application/pdf")
    message.send(fail_silently=False)

    logger.info("License email '%s' sent to %s", licence.internal_id, licence.licensee_email)
    return True


def send_release_notification(release) -> int:
    from .models import Team

    recipients = Team.objects.filter(is_blacklist=False, is_disconnected=False).values_list("email", flat=True)
    subject_parts = [part for part in ["New Release", release.artist, release.title] if part]
    subject = " — ".join(subject_parts) if subject_parts else "New Release"

    context = {
        "release": release,
    }

    sent = send_templated_email(subject, recipients, "emails/release_notification.html", context)
    logger.info("Release notification for '%s' sent to %s recipient(s)", release, sent)
    return sent
