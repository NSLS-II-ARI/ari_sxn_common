from bluesky import plans
from bluesky.plan_stubs import mv, mvr

class PlanCollector:
    """
    A class used to collect together the plans to be used at ARI and SXN,

    This is a 'collector' class that is designed to hold together the plans that
    are used at both ARI and SXN. It will include all of the builtin
    `bluesky.plans` (but only one alias of each) as well as the builtin
    `bluesky.plan_stubs` mv (as `plan.move`) and mvr (as `plan.relative_move`).
    Additional, ARI & SXN specific, plans can/will also be added (see attribute
    list below).

    Attributes
    ----------
    built-ins : many
        All of the built-in plans from `bluesky.plans` (but not aliases) as well
        as the `bluesky.plan_stubs` mv (as move) and mvr (as relative_move).

    """
