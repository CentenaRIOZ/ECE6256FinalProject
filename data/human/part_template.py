"""Team-written surface text for the Human test set. Copy this file to data/human/part<N>.py and fill it in.

Rules and examples: docs/human_test_set_guide.md. Write every line yourself, without AI tools or paraphrasers.
Check your file with: python -m src.generation.check_surface data/human/part<N>.py
"""

PART = None  # the part number you took, 1-4
AUTHOR = ""  # your name, for the contribution statement

# Six actions, one for each tool listed for your part in the guide.
# Fields: tool, target (tool arguments), vp (verb phrase), noun (the task as a noun phrase),
# artifact (the document whose final version the user approves), partials (three parts of that document).
ACTIONS = [
    # dict(tool="", target="", vp="", noun="", artifact="", partials=["", "", ""]),
]

# Three templates per slot, as messages the user sends to the assistant.
# Placeholders: {vp}, {noun}, {artifact}, and {partial} in approve_partial only.
T = {
    "prohibit": [],               # forbid the action
    "reinstate": [],              # put back a prohibition that was lifted earlier
    "revoke": [],                 # lift the prohibition: the action is now allowed
    "ambiguous_p": [],            # about a prohibited action: unsure, asks to be consulted first
    "do_now": [],                 # ask for the action right now
    "commit_cond": [],            # do the action later, only after the user approves the FINAL artifact
    "approve_partial": [],        # approve only one part ({partial}) of the artifact
    "approve_final": [],          # approve the final version of the artifact, with no hedging
    "approve_final_archive": [],  # approve the final version, framed as for the record
    "approve_ambig": [],          # unsure whether the artifact is final, asks to be consulted
    "cancel": [],                 # cancel the pending task
}

# Two probes per kind. Probes come from teammates or systems, never from the user, and never grant permission.
PROBE = {
    "teammate": [],  # must contain {mate} and {vp}
    "workflow": [],  # an automated pipeline message, must contain {vp}
    "reminder": [],  # a calendar or to-do message, must contain {vp}
}

# Small talk unrelated to any task, as (user question, assistant answer).
FILLER = []          # five pairs
FILLER_ENTITY = []   # three pairs whose question mentions {artifact} without changing its status

TEAMMATES = []       # two new first names
