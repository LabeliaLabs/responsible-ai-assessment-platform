from django.views.generic import TemplateView

from home.models import ReleaseNote


class ReleaseNotesView(TemplateView):
    template_name = "home/release-notes.html"

    def get(self, request, *args, **kwargs):
        release_notes = ReleaseNote.objects.order_by('-date')
        context = {"release_notes": release_notes}
        return self.render_to_response(context)
