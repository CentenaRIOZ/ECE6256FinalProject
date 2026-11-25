"""Wording cues that each event type must keep, shared by the paraphrase filter and the surface-text checker."""

CUES = {
    "prohibit": ["not", "n't", "never", "no ", "avoid", "hold off", "ban", "stop", "forbid"],
    "reinstate": ["not", "n't", "never", "no ", "avoid", "hold off", "ban", "stop", "forbid"],
    "ambiguous_p": ["ask", "check", "confirm", "ping", "run it by"],
    "approve_ambig": ["ask", "check", "confirm", "ping", "run it by"],
    "cancel": ["cancel", "drop", "forget", "no longer", "no need", "scrap", "call off", "don't need"],
    "commit_cond": ["final"], "approve_final": ["final"], "approve_final_archive": ["final"],
}
NEG_FORBIDDEN = {"approve_partial": ["final"]}  # a partial approval must not mention 'final'
