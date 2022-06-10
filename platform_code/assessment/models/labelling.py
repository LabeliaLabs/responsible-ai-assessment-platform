from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .evaluation import Evaluation


class Labelling(models.Model):
    """
    This class defines the labelling objects which ae used to label an evaluation and
    therefore the organisation.
    A labelling object is bound to one evaluation and one evaluation can be linked
    to different labelling objects.
    A labelling object is defined by a status, which describes the status of the labelling process
    for the evaluation by Labelia Labs.
    Last update field is used to store the date of the last
    """
    evaluation = models.OneToOneField(Evaluation, on_delete=models.CASCADE)
    PROGRESS = "progress"
    JUSTIFICATION = "justification"
    LABELLED = "labelled"
    REFUSED = "refused"

    STATUS = (
        (PROGRESS, _("progress")),
        (JUSTIFICATION, _("justification")),
        (LABELLED, _("labelled")),
        (REFUSED, _("refused"))
    )
    status = models.CharField(max_length=200, choices=STATUS, default=PROGRESS)
    counter = models.IntegerField(default=1)
    start_date = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(blank=True, null=True)
    justification_request_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Label of the evaluation id={self.evaluation.id}"

    @classmethod
    def create_labelling(cls, evaluation):
        if evaluation.is_finished:
            labelling = cls(evaluation=evaluation, last_update=timezone.now())
            labelling.save()
            evaluation.freeze_evaluation()
            return labelling

    def set_justification_required(self):
        """
        Sets the status as 'justification' and thus the evaluation is editable again
        """
        self.status = Labelling.JUSTIFICATION
        self.justification_request_date = timezone.now()
        self.save()
        self.evaluation.is_editable = True
        self.evaluation.save()

    def submit_again(self):
        """
        Increments the counter - used when user submit again the labelling process
        and set the status to "progress"
        """
        self.counter += 1
        self.status = Labelling.PROGRESS
        self.evaluation.freeze_evaluation()
        self.last_update = timezone.now()
        self.save()

    def set_final_status(self, status):
        """
        This method is used to reject/validate a labelling process ie set the status to "refused"/"labelled"
        The evaluation cannot be modified anymore nor deleted.
        """
        if status == "rejection":
            self.status = Labelling.REFUSED
        elif status == "validation":
            self.status = Labelling.LABELLED
        self.evaluation.freeze_evaluation()
        self.save()
