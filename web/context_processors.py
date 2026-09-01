"""Template context shared by every page.

The site is English-only. This used to publish the active language and a
switcher URL; both went when the second locale did, and what is left is a
placeholder so the context-processor slot in settings stays wired up for the
next thing that needs it.
"""


def site_context(request):
    return {}
