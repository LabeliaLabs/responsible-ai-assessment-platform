from .duplicate import duplicateView  # noqa
from .evaluation import DeleteEvaluation, EvaluationCreationView, EvaluationView  # noqa
from .labelling import (  # noqa
    labellingAgainView,
    labellingEnd,
    labellingJustification,
    labellingView,
)
from .organisation import SummaryView, leave_organisation  # noqa
from .results import ResultsView  # noqa
from .resultsPDF import ResultsPDFView  # noqa
from .section import SectionView  # noqa
from .upgrade import upgradeView  # noqa
