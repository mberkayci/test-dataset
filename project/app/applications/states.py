from enum import StrEnum


class ApplicationState(StrEnum):
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


# &begin[ChangeState]
# The pipeline only moves forward: applied -> screening -> interview -> offer.
# Screening may be skipped (some companies invite straight to interview), but an
# offer always requires an interview. Rejected and withdrawn are final; either can
# happen at any active stage (an offer can be rescinded or declined).
ALLOWED_TRANSITIONS: dict[ApplicationState, frozenset[ApplicationState]] = {
    ApplicationState.APPLIED: frozenset(
        {ApplicationState.SCREENING, ApplicationState.INTERVIEW,
         ApplicationState.REJECTED, ApplicationState.WITHDRAWN}
    ),
    ApplicationState.SCREENING: frozenset(
        {ApplicationState.INTERVIEW, ApplicationState.REJECTED, ApplicationState.WITHDRAWN}
    ),
    ApplicationState.INTERVIEW: frozenset(
        {ApplicationState.OFFER, ApplicationState.REJECTED, ApplicationState.WITHDRAWN}
    ),
    ApplicationState.OFFER: frozenset({ApplicationState.REJECTED, ApplicationState.WITHDRAWN}),
    ApplicationState.REJECTED: frozenset(),
    ApplicationState.WITHDRAWN: frozenset(),
}


class InvalidStateTransition(Exception):
    def __init__(self, current: ApplicationState, target: ApplicationState):
        self.current = current
        self.target = target
        allowed = sorted(s.value for s in ALLOWED_TRANSITIONS[current])
        if current == target:
            reason = f"Application is already in state '{current}'."
        elif not allowed:
            reason = f"Application is in final state '{current}' and cannot be changed."
        else:
            reason = (
                f"Cannot change state from '{current}' to '{target}'. "
                f"Allowed next states: {', '.join(allowed)}."
            )
        super().__init__(reason)


def ensure_transition_allowed(current: ApplicationState, target: ApplicationState) -> None:
    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidStateTransition(current, target)
# &end[ChangeState]
