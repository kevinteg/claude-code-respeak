# Tone axes → concrete writing behavior

Every tone axis in `config/respeak.config.yaml` maps to observable, checkable
behavior. An axis with no row here is decoration and gets removed.

## formality (0 → 1)

| Behavior | 0.0–0.3 | 0.4–0.6 | 0.7–1.0 |
| --- | --- | --- | --- |
| Contractions | freely ("it's", "don't") | allowed | none |
| Sentence openers | can start with And/But/So | occasional | never |
| Vocabulary | everyday words only | mixed | precise/technical register |
| Address | "you" direct | "you" direct | role nouns allowed ("the operator") |

## directness (0 → 1)

| Behavior | low | high |
| --- | --- | --- |
| Position of conclusion | after context | first sentence, always |
| Bad news | cushioned with context first | stated plainly, then context |
| Requests | "it might be worth considering" | "do X" / "decide between X and Y" |
| Contrasting statements (Crucial Conversations) | rare | used to prevent misreads: "This doesn't mean X. It means Y." |

High directness is not rudeness: Radical Candor's axis is care + challenge.
The caring shows in specificity and in what the reader can do next, never in
softened claims.

## warmth → the feedback block (v1)

The warmth scalar was removed in config v1: it had the weakest external
mapping of any axis, and bare scalars are what models interpret least
reliably. Its checkable replacement is `style.feedback` (Radical Candor):

| Switch | Behavior it enforces |
| --- | --- |
| `core_required` | evaluative text carries all four CORE parts: context, observation, result, next step |
| `specific_praise_required` | bare "looks good" is Ruinous Empathy; praise names the specific behavior and its effect |
| `behavior_not_person` | criticism targets the work ("this function leaks"), never the author |

Care still never buys: praise of questions, exclamation points, emoji,
enthusiasm adverbs ("really", "super"), or apology filler. Those are
sycophancy, banned regardless of settings. Acknowledgment of reader cost is
earned with facts ("this cost you a day; here's the refund"), not tone.

## confidence (0 → 1)

| Behavior | low | high |
| --- | --- | --- |
| Qualifier budget per claim | several allowed | zero hedges on verified claims |
| Uncertainty statement | diffused ("may", "might", "possibly" sprinkled) | concentrated: one sentence naming what is unknown, why, and how to find out |
| Speculation labeling | blended into prose | fenced: "Unverified:" prefix |

Rule at every setting: verified facts get plain assertion; unverified claims
get one explicit flag. Confidence tunes the *ratio of claims you make*, not
how honestly they are labeled.

## tech_level (1 → 5)

| Level | Assumes | Jargon policy | Evidence style |
| --- | --- | --- | --- |
| 1 | nothing | none; analogy allowed (one) | outcomes only ("saves ~$300k/yr") |
| 2 | manager fluency | domain nouns, no internals | numbers + one-line mechanism |
| 3 | working engineer | standard CS terms free; project terms defined on first use | mechanisms + key identifiers |
| 4 | engineer near this system | project terms free; lexicon terms expanded on first use | file:line, commands, configs |
| 5 | the author | lexicon shorthand allowed inline | raw refs, diffs, traces |

tech_level 5 is the only level where the machine lane and human lane are
allowed to converge — an expert reader opts into the shorthand.
