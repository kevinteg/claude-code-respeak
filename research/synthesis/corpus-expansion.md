All four files read. The seed has 6 categories (~60 entries) and 25 replacement pairs (corpus/banned-phrases.yaml:9-103, corpus/replacements.yaml:8-42). The research supports a large expansion. Everything below is traceable to a section of `research/sources/deai-language-landscape.md` (cited as **deai §n**) or `research/sources/style-as-code-tooling.md` (**sac §n**); I've added no invented tells.

One flavor constraint I carried through: sac §1 notes all current patterns are RE2-safe (no lookahead/backrefs) because the planned Vale compile target requires it (style-as-code-tooling.md:49) — every new pattern below is also RE2-safe.

## 1. New banned-phrase entries

```yaml
# --- ADDITIONS to corpus/banned-phrases.yaml ---
# Every entry cites its research grounding. New categories cite the section
# that justifies them in the category note.

categories:

  # ================= additions to EXISTING categories =================

  pleasantries:
    # new entries from WP:CERTAINLY, deai §1.1 (line 24) — "unambiguous" tier
    entries:
      - { pattern: 'would you like (me to|a|more)', severity: error }             # deai §1.1 WP:CERTAINLY
      - { pattern: '\bis there anything else\b', severity: error }                # deai §1.1 WP:CERTAINLY
      - { phrase: I hope this message finds you well, severity: error }           # deai §1.1, §1.5
      - { pattern: "^here('s| is) (a|an|the)\\b", severity: warn }                # deai §1.1 "here is a…"
      - { pattern: '\bmore detailed breakdown\b', severity: warn }                # deai §1.1 WP:CERTAINLY
      - { pattern: "I('d| would) be happy to\\b", severity: error }               # deai §3.11; broader than seed's "happy to (help|assist)"

  ai_cliches:
    # new entries from WP:AIVOCAB (deai §1.2), Kobak 2025 excess-vocab list
    # (deai §2.1, lines 99-113), WP:AIPUFFERY (deai §1.1), antislop corpus (deai §7)
    entries:
      - { pattern: '\bpivotal\b', severity: error, fix: name what it decides }    # deai §1.2 + §2.1 (Liang top-4 word)
      - { pattern: '\bintricate(ly)?\b|\bintricac(y|ies)\b', severity: error }    # deai §1.2, §2.1 (Gray 2024: 2x in 2023)
      - { pattern: '\bmeticulous(ly)?\b', severity: error, fix: careful(ly) }     # deai §1.2, §2.2 (arXiv:2508.01930)
      - { pattern: '\bunderscor(e|es|ed|ing)\b', severity: error, fix: shows / stresses }  # deai §2.1 (r=13.8)
      - { pattern: '\bshowcas(e|es|ed|ing)\b', severity: error, fix: shows }      # deai §2.1 (r=10.7)
      - { pattern: '\brevolutioniz(e|es|ed|ing)\b', severity: error }             # deai §2.1, §7
      - { pattern: '\bvaluable insights\b', severity: error }                     # deai §1.1 WP:SUPERFICIAL
      - { pattern: '\bdiverse array\b', severity: error, fix: list them }         # deai §1.1 WP:AIPUFFERY
      - { pattern: '\brich cultural heritage\b', severity: error }                # deai §1.1 WP:AIPUFFERY
      - { pattern: '\b(breathtaking|stunning natural beauty)\b', severity: error } # deai §1.1 WP:AIPUFFERY
      - { pattern: '\bever.?(evolving|changing)\b', severity: error }             # deai §7 antislop
      - { pattern: "(today's|in today's) digital (age|era)", severity: error }    # deai §7 antislop (attested forms)
      - { pattern: '\bindelible( mark)?\b', severity: error }                     # deai §1.1 WP:AILEGACY + §7
      - { pattern: '\bkaleidoscope\b', severity: error }                          # deai §7 antislop
      - { pattern: '\bsymphony of\b', severity: error }                           # deai §7 antislop
      - { pattern: '\bdeep dive\b', severity: warn, fix: close look }             # deai §1.2 WP:AIVOCAB
      - { pattern: '\bbolster(s|ed|ing)?\b', severity: warn, fix: support }       # deai §1.2 (2023-2025 era lists)
      - { pattern: '\bgarner(s|ed|ing)?\b', severity: warn, fix: get / win }      # deai §1.2
      - { pattern: '\binterplay\b', severity: warn }                              # deai §1.2, §2.1
      - { pattern: '\bvibrant\b', severity: warn }                                # deai §1.1 puffery + §1.2 vocab
      - { pattern: '\brealm(s)?\b', severity: warn, fix: field / area }           # deai §2.1 (Liang top-4), §7
      - { pattern: '\bgroundbreaking\b', severity: warn, fix: say what it did first } # deai §1.1, §2.1
      - { pattern: '\brenowned\b', severity: warn, fix: well-known / known for X } # deai §1.1, §2.1
      - { pattern: '\bin the heart of\b', severity: warn }                        # deai §1.1 WP:AIPUFFERY
      - { pattern: '\bcutting.?edge\b', severity: warn }                          # deai §7 antislop
      - { pattern: '\bwhen it comes to\b', severity: warn, fix: for / about }     # deai §7 antislop
      - { pattern: '\bunparalleled\b', severity: warn }                           # deai §2.1 style list
      - { pattern: '\binvaluable\b', severity: warn }                             # deai §2.1 style list
      - { pattern: '\bshed(ding|s)? light\b', severity: warn, fix: show / explain } # deai §2.1
      - { pattern: '\bpav(e|es|ed|ing) the way\b', severity: warn }               # deai §2.1 ("paving")
      - { pattern: '\bpoised to\b', severity: warn }                              # deai §2.1
      - { pattern: '\btransformative\b', severity: warn }                         # deai §2.1
      - { pattern: '\bburgeoning\b', severity: warn, fix: growing }               # deai §2.1
      - { pattern: '\bunveil(s|ed|ing)?\b', severity: warn, fix: show / release } # deai §2.1
      - { pattern: '\bembark(s|ed|ing)?\b', severity: warn, fix: start }          # deai §7 antislop
      - { pattern: '\bnuanced?\b|\bnuances\b', severity: warn }                   # deai §2.1
      - { pattern: '\b(align|resonate)s? with\b', severity: warn }                # deai §1.1 WP:SUPERFICIAL, §1.2 (2024-25 era)
      - { pattern: '\bamidst\b', severity: warn, fix: amid / among }              # deai §2.1, §7
      - { pattern: '\bakin to\b', severity: warn, fix: like }                     # deai §2.1
      - { pattern: '\bunderpin(s|ned|ning)?\b', severity: warn }                  # deai §7 antislop
      - { pattern: '\bdaunting\b', severity: warn }                               # deai §7 antislop
      - { pattern: '\benduring\b', severity: warn }                               # deai §1.1 AILEGACY + §1.2 vocab
      - { pattern: '\bcrucial\b', severity: warn, fix: say why it matters }       # deai §2.1 (δ=0.037; common tier — density, not per-hit)
      - { pattern: '\benhanc(e|es|ed|ing)\b', severity: warn, fix: improve }      # deai §1.2 (2024-25 era), §2.1 common set
      - { pattern: '^additionally,', severity: warn, fix: also }                  # deai §1.2 "Additionally (sentence-initial)"
      - { pattern: '^(moreover|furthermore),', severity: warn }                   # deai §7 antislop; density-based per §2.1

  hedging:
    entries:
      - { pattern: '\bit is advisable\b', severity: warn }                        # deai §7 antislop
      - { pattern: '\byou may want to\b', severity: warn }                        # deai §7 antislop
      - { pattern: '\bthere are a few considerations\b', severity: warn }         # deai §7 antislop

  self_narration:
    entries:
      - { pattern: 'as previously (mentioned|noted|discussed)', severity: warn,
          fix: repeat the fact }                                                  # deai §7; fills word-order gap in seed line 93
      - { pattern: '\bto put it simply\b', severity: warn }                       # deai §7 antislop
      - { pattern: '^remember that\b', severity: warn }                           # deai §7 antislop

  # ======================= NEW categories =======================

  significance_inflation:
    note: >
      Undue emphasis on significance/legacy — grading importance instead of
      stating mechanism. Source: deai §1.1 (WP:AILEGACY / WP:AITREND, "strong"
      tier) and deai §3 tone item 15; root-cause framing deai §1 ("less
      specific and more exaggerated").
    entries:
      - { pattern: 'highlight(s|ing) (its|the) (importance|significance)', severity: error }
      - { pattern: '\bkey turning point\b', severity: error }
      - { pattern: '\bevolving landscape\b', severity: error }
      - { pattern: 'symboliz(es|ing) (its |the )?(ongoing|enduring|lasting)', severity: error }
      - { pattern: '(represents|marks) a (significant |major |notable )?shift', severity: warn }
      - { pattern: '\bsetting the stage for\b', severity: warn }
      - { pattern: '\bfocal point\b', severity: warn }
      - { pattern: '\breflects broader\b', severity: warn }
      - { pattern: '\bdeeply rooted\b', severity: warn }
      - { pattern: '\b(marking|shaping) the\b', severity: warn }
      - { pattern: "\\bit('s| is) essential to\\b", severity: warn }              # deai §7
      - { pattern: '\bkey (factor|driver|moment|component|element)\b', severity: warn }  # deai §1.2 "key (adjective)"

  copula_avoidance:
    note: >
      Elaborate verbs where "is/has" is meant. Source: deai §1.2 (WP:AINOCOPULA;
      measured >10% drop of is/are in 2023 academic text), §3.21, and the fix
      pattern in deai §6.2 ("restore the copula").
    entries:
      - { pattern: '\b(stands|serves) as\b', severity: warn, fix: is }
      - { pattern: '\bfunctions as\b', severity: warn, fix: is / works as }
      - { pattern: '\boperates as\b', severity: warn, fix: is / runs as }
      - { pattern: '\brepresents a\b', severity: warn, fix: is a }
      - { pattern: '\brefers to\b', severity: warn, fix: "in definitions, write 'X is …'" }

  participial_tails:
    note: >
      Sentence-final present-participle clauses bolted onto facts. Source: deai
      §1.1 (WP:SUPERFICIAL, "strong"), §2.3 (Reinhart et al., PNAS 2025 —
      measured overuse of present participial clauses), §3.10; fix per §6.3
      ("chop sentence-final participles").
    entries:
      - { pattern: ',\s(highlighting|underscoring|emphasizing|reflecting|symbolizing|signifying|showcasing)\b',
          severity: error, fix: end the sentence at the fact, or make the claim its own sentence with an agent }
      - { pattern: ',\s(ensuring|fostering|cultivating|encompassing|enhancing)\b', severity: warn,
          fix: same — delete the clause or give it an agent }
      - { pattern: ',\scontributing to\b', severity: warn }

  weasel_attribution:
    note: >
      Vague attribution and canned notability claims. Source: deai §1.1
      (WP:AIWEASEL "medium"; WP:AIATTR "strong, more common in 2025+ models"),
      §3.14 and §3.20; fix per §6.6 ("attribute or delete").
    entries:
      - { pattern: '\b(experts|observers|critics|analysts) (argue|say|note|suggest|have cited)\b',
          severity: error, fix: name the person and source, or cut }
      - { pattern: '\bmaintains an active social media presence\b', severity: error }
      - { pattern: '\bwritten by a leading expert\b', severity: error }
      - { pattern: '\b(local|regional|national) media outlets\b', severity: error }
      - { pattern: '\bindustry reports\b', severity: warn, fix: which report? cite it }
      - { pattern: '\bwidely (regarded|considered|seen|held)\b', severity: warn, fix: by whom? }
      - { pattern: '\bseveral (sources|publications|studies|outlets)\b', severity: warn, fix: count them and cite }
      - { pattern: '\bindependent coverage\b', severity: warn }

  knowledge_cutoff:
    note: >
      Model-disclaimer language leaking into documents. Source: deai §1.1
      (WP:AICUTOFF — "unambiguous" tier), hence all error.
    entries:
      - { pattern: 'as of my (last|latest) knowledge update', severity: error }
      - { pattern: 'while specific details (are|remain) (limited|scarce)', severity: error }
      - { pattern: 'not widely (available|documented|disclosed)', severity: error }
      - { pattern: '\bbased on available information\b', severity: error }
      - { pattern: '\bmaintains a low profile\b', severity: error }

  machine_artifacts:
    note: >
      Literal tool residue — never legitimate in output. Source: deai §1.4
      (tool-specific artifacts) and §1.1 (WP:AIPLACEHOLDER). All error.
    entries:
      - { pattern: 'oai_citation|oaicite|contentReference|attributableIndex', severity: error }
      - { pattern: 'citeturn\d|turn\d+(search|image|news)\d+', severity: error }
      - { pattern: 'utm_source=(chatgpt\.com|openai|copilot\.com)', severity: error }
      - { pattern: '\[cite: ?\d+\]|\(start_span\)|\(end_span\)', severity: error }
      - { pattern: 'grok-card|grok_render_citation_card_json|referrer=grok\.com', severity: error }
      - { pattern: '【\d+†', severity: error }
      - { pattern: '\[attached_file:\d+\]|\[web:\d+\]|ppl-ai-file-upload', severity: error }
      - { pattern: ':::writing\{', severity: error }
      - { pattern: '\[(Your Name|Specific Topic)\]|INSERT_SOURCE_URL|PASTE_[A-Z_]*URL', severity: error }

  negative_parallelism:
    note: >
      The "It's not X — it's Y" family. Source: deai §1.2 (WP:AIPARALLEL),
      §3.13 ("reads as clearing up a misconception nobody had"); antislop ships
      regex bans for this family (deai §5). Seed already covers "not just X,
      but" (banned-phrases.yaml:65); these are the stronger em-dash/triple forms.
    entries:
      - { pattern: "it('s| is) not [^.]{3,40}[,;]? ?(—|–|-)? ?it('s| is)\\b", severity: error,
          fix: assert Y directly }
      - { pattern: "\\bisn't [^.]{3,40}\\s*(—|–)\\s*it('s| is)\\b", severity: error }
      - { pattern: '\bno \w+, no \w+, just \w+', severity: error }

  condescension:
    note: >
      Minimizing difficulty at the reader. Source: sac §6 (Google style guide
      avoid-list — "simply / it's easy / just / quickly in procedures"),
      sac §2 (alex — condescending language: "obviously", "everyone knows"),
      and sac §9 gap 9, which recommends exactly this category.
    entries:
      - { pattern: '\beveryone knows\b', severity: error }
      - { pattern: '\bsimply (click|run|open|add|type|install|select)\b', severity: warn, fix: drop "simply" }
      - { pattern: '\bjust (click|run|open|add|type|install|select)\b', severity: warn, fix: drop "just" }
      - { pattern: "\\bit('s| is) (easy|simple|straightforward) to\\b", severity: warn }
      - { pattern: '\bobviously\b', severity: warn }
      - { pattern: '!', severity: warn,
          fix: end with a period; budget ≤1 per document outside quotes }        # sac §6 Google; sac §9 gap 10

  claude_reflexes:
    note: >
      Chat voice leaking into documents — Claude-specific conversational
      reflexes. Source: deai §4 ("Claude conversational reflexes") plus
      WP:CERTAINLY (deai §1.1) for the verbatim-listed items.
    entries:
      - { pattern: "you('re| are) absolutely right", severity: error }            # deai §1.1 lists it verbatim
      - { pattern: '\b(great|good) catch\b', severity: warn }
      - { pattern: '\bI appreciate you\b', severity: warn }
      - { pattern: '\blet me be (direct|clear|blunt)\b', severity: warn, fix: just be it }
      - { pattern: '^to be fair,', severity: warn }
      - { pattern: '^that said,', severity: warn, fix: density-based; one pivot per document }
      - { pattern: '^(importantly|crucially|critically),', severity: warn, fix: show the importance, do not announce it }
      - { pattern: '\bgenuinely\b', severity: warn }
      - { pattern: '\bdeeply (personal|felt|human|moving)\b', severity: warn }
      - { pattern: '\bquietly (one of )?the most\b', severity: warn }
      - { pattern: '\bin many ways\b', severity: warn }
      - { pattern: '\bat its core\b', severity: warn }
      - { pattern: '^fundamentally,', severity: warn }
      - { pattern: "the way I('d| would) think about (this|it)", severity: warn }

  self_grading:
    note: >
      Editorial frames that announce the prose's quality instead of exhibiting
      it — extensions of the user_banned family. Source: deai §4 ("Self-grading
      editorial frames"; analysis of the project-ban generator).
    entries:
      - { pattern: '\bthe honest version\b', severity: error }                    # extends banned root, seed line 21
      - { pattern: '\bthe sharpest version\b', severity: error }                  # extends banned root, seed line 24
      - { pattern: 'a sharper way to (say|put)', severity: warn }
      - { pattern: "if I('m| am) being honest", severity: warn }
      - { pattern: '\bto be blunt\b', severity: warn }
      - { pattern: '^frankly,', severity: warn }
      - { pattern: 'the real (question|story|work|issue) is', severity: warn }
      - { pattern: 'the key insight( here)? is', severity: warn }
      - { pattern: "here('s| is) the thing", severity: warn }
      - { pattern: '^(the short version|tl;?dr):', severity: warn }
      - { pattern: 'what actually matters( here)?', severity: warn }
      - { pattern: '\btighter (framing|version|phrasing)\b', severity: warn }
      - { pattern: 'a cleaner way to (put|say)', severity: warn }
      - { pattern: '\bpunch(y|ier)\b', severity: warn }
      - { pattern: "(this|that) (lands|doesn't land)\\b", severity: warn }
      - { pattern: '\bdoes a lot of (the )?work\b', severity: warn }              # cousin of "load-bearing"
      - { pattern: '\bcarries the weight\b', severity: warn }
      - { pattern: '\bearns (its place|the reader)', severity: warn }

  anatomy_metaphors:
    note: >
      Structure-as-body metaphors — same generator as the project-banned
      "spine"/"load-bearing" family. Source: deai §4 ("Structure-as-anatomy
      metaphors", with proposed severities followed here).
    entries:
      - { pattern: '\bconnective tissue\b', severity: error }
      - { pattern: '\bbeating heart of\b', severity: error }
      - { pattern: '\bthe backbone of\b', severity: warn, fix: name the actual structure }
      - { pattern: '\b(the skeleton of|skeletal structure)\b', severity: warn }
      - { pattern: '\bthe scaffolding\b', severity: warn }
      - { pattern: '\bheavy lifting\b', severity: warn }
      - { pattern: '\bthrough.?line\b', severity: warn }
      - { pattern: '\b(connective thread|thread that runs through)\b', severity: warn }
      - { pattern: '(gives?|adds?) [^.]{0,25}\bmuscle\b', severity: warn }

  formulaic_structure:
    note: >
      Rigid outline formulas. Source: deai §1.1 (WP:FACESCHALLENGES — "strong;
      it's the rigid formula, not the topic"; "Awards and recognition" and
      title-as-proper-noun leads, both "medium") and deai §3 structure items 2-4.
    entries:
      - { pattern: '\bfaces several challenges\b', severity: error }
      - { pattern: '\bdespite these challenges\b', severity: error }
      - { pattern: '\b(challenges and legacy|future (outlook|prospects))\b', severity: warn }
      - { pattern: '\bawards and recognition\b', severity: warn }
      - { pattern: '(is|refers to) a curated (compilation|list|selection)', severity: warn }

  vague_association:
    note: >
      Naming proximity instead of the relation. Source: deai §1.2 (WP:AICONNECT),
      §3.22; fix per §6.4 ("name the relation").
    entries:
      - { pattern: '\bin connection (with|to)\b', severity: warn, fix: for / about / over }
      - { pattern: '\bin association with\b', severity: warn }
      - { pattern: '\bassociated with\b', severity: warn,
          fix: used for / caused by / part of — name the relation. Legitimate in statistics; needs an exceptions mechanism }

  format_tells:
    note: >
      Punctuation/formatting fingerprints. Source: deai §1.3 (WP:AIDASH,
      WP:AIEMOJI, WP:AILIST, curly quotes, thematic breaks) and §3 structure
      items 5-9; §3.18 notes the July 2026 finding that Claude is the only
      major model still above professional-writer em-dash rates — a
      Claude-specific severity bump for this project.
    entries:
      - { pattern: ' — ', severity: warn,
          fix: density-based — restructure the sentence; Claude-specific tell }
      - { pattern: '[""]', severity: warn, fix: straight quotes; curly quotes signal pasted ChatGPT/DeepSeek text }
      - { pattern: '^\s*[-•*]\s*\*\*[^*]+\*\*:', severity: warn, fix: bold-label bullets read as AI; write prose }
      - { pattern: '(🧠|🧱|🚨|🧭|📌|🚀|✅|✨|💡)', severity: error, fix: no emoji decoration }
      - { pattern: '^-{3,}$', severity: warn, fix: thematic-break litter; cut }

  narrative_slop:
    note: >
      Stock narrative phrasing, for storytelling/ELI5 modes. Source: deai §7
      (antislop corpus, "Narrative slop" family; author warns list is
      uncurated — errors here are limited to full stock phrases).
    entries:
      - { phrase: barely above a whisper, severity: error }
      - { pattern: 'shivers? (down|up) (his|her|their|my|the) spine', severity: error }
      - { phrase: with practiced ease, severity: error }
      - { pattern: 'like a moth to a flame', severity: error }
      - { pattern: 'little did (he|she|they) know', severity: error }
      - { phrase: life would never be the same, severity: error }
      - { phrase: for what seemed like an eternity, severity: error }
      - { phrase: 'maybe, just maybe', severity: error }
      - { phrase: 'for now, that was enough', severity: error }
      - { phrase: reckless abandon, severity: error }
      - { phrase: humble abode, severity: error }
      - { pattern: '\b(palpable|cacophony|gossamer|rivulets|ministrations)\b', severity: warn }
      - { pattern: '\b(thrummed|rasped|glinting|twinkled)\b', severity: warn }
      - { pattern: '\b(conspiratorially|mischievously|quizzically|sagely|reassuringly)\b', severity: warn }

  stock_names:
    note: >
      LLM default-name basin for invented examples. Source: deai §7, which
      flags this as a "novel category". Case-insensitive matching may collide
      with real names — hence warn for names real people carry.
    entries:
      - { pattern: '\b(Elara|Elysia|Eldoria|Atheria|Zephyria|Whisperwood|Oakhaven|Ravenswood|Kael)\b',
          severity: error, fix: pick a name outside the LLM default basin }
      - { pattern: '\b(Lyra|Eira|Jaxon|Elias)\b', severity: warn,
          fix: fine for real people; avoid as invented-character defaults }
```

That is ~130 new entries across 6 extended and 14 new categories — well past the 40 target, all sourced.

## 2. New replacement pairs

```yaml
# --- ADDITIONS to corpus/replacements.yaml ---

replacements:
  # Copula restoration (deai §1.2 WP:AINOCOPULA; fix pattern deai §6.2:
  # "serves as the exhibition arm" -> "is the exhibition space")
  - { from: serves as, to: is }
  - { from: stands as, to: is }
  - { from: functions as, to: is / works as }
  - { from: represents a, to: is a }
  - { from: refers to, to: is, note: definitions only }
  - { from: boasts, to: has }                       # deai §6.2 verbatim ("boasts 8 tracks" -> "has 8 tracks")
  - { from: maintains a, to: has a, note: when "has" is meant }   # deai §1.2

  # Relation naming (deai §1.2 WP:AICONNECT; deai §6.4)
  - { from: associated with, to: used for / caused by / part of, note: name the relation }
  - { from: in connection with, to: for / about / over }

  # AI-vocab -> plain verb (deai §1.2 WP:AIVOCAB; deai §2.1 Kobak style list)
  - { from: showcases, to: shows }
  - { from: underscores, to: shows / stresses }
  - { from: highlights, to: shows, note: verb use }
  - { from: garner, to: get / win }
  - { from: bolster, to: support / strengthen }
  - { from: meticulously, to: carefully }
  - { from: intricate, to: detailed / complex }
  - { from: amidst, to: amid / during }
  - { from: akin to, to: like }
  - { from: burgeoning, to: growing }
  - { from: renowned, to: well-known }
  - { from: deep dive, to: close look }
  - { from: enhance, to: improve }
  - { from: elucidate, to: explain }
  - { from: necessitates, to: requires }
  - { from: endeavors, to: efforts }
  - { from: exhibited, to: showed }                 # deai §2.1 common-marker set
  - { from: comprehensive, to: complete / full }    # deai §2.1 common-marker set

  # Rewrite-patterns, not word swaps
  - from: a diverse array of
    to: "list the actual items"
    note: rewrite-pattern (deai §1.1 WP:AIPUFFERY)
  - from: "it's not X — it's Y"
    to: "assert Y directly"
    note: rewrite-pattern (deai §3.13)
  - from: please note that
    to: "(delete)"
    note: placeholder phrase (sac §6, Google avoid-list)
  - { from: at this time, to: now / currently }     # sac §6, Google avoid-list
  - from: "there is / there are (sentence-initial)"
    to: "name the real subject"
    note: rewrite-pattern (sac §2 write-good `thereIs`; sac §6 Microsoft tip 10)

  # Contractions — conditional on formality setting (sac §6 Microsoft tip 3:
  # "project friendliness = use contractions"; sac §9 gap 6)
  - { from: it is, to: "it's", note: when formality is low; gate on config }
  - { from: you will, to: "you'll", note: same gate }
  - { from: we are, to: "we're", note: same gate }
```

35 pairs — past the 20 target.

## 3. Seed entries the research contradicts or suggests re-scoring

**Too lax (upgrade warranted):**

1. **`boasts` warn → error** (banned-phrases.yaml:55). Triple-sourced: WP:AIPUFFERY "strong" tier (deai-language-landscape.md:18), WP:AIVOCAB footnoted list (line 29), and Kobak's rare style list (line 111). Same evidence class as `delve`/`tapestry`, which the seed treats as error.
2. **`let me know if you('d| would)? like` warn → error** (banned-phrases.yaml:43-45). WP:CERTAINLY classifies "let me know" as **unambiguous** chatbot voice (deai-language-landscape.md:24) — the seed's own convention puts unambiguous tells at error (cf. "I hope this helps", line 35, error, same source row).
3. **`seamless(ly)` warn → error** (banned-phrases.yaml:59). Appears in Kobak's rare style list (line 111) — the per-occurrence-flaggable tier, unlike the "common but excess" density tier (line 113).
4. **`foster(s|ing)?` — split severities** (banned-phrases.yaml:74). "fostering" specifically is in the mid-2024–2025 era vocab list (line 33), WP:SUPERFICIAL (line 17), and Kobak's list (line 111); the `-ing` form justifies error while bare "foster" stays warn.
5. **`happy to (help|assist)`** (banned-phrases.yaml:41-42) — coverage gap rather than severity: the attested form is "I'd be happy to…" with any verb (deai-language-landscape.md:149). Added the broader pattern above.

**Too strict or evidence-light (keep only on owner authority, and say so):**

6. **`crisp`** (banned-phrases.yaml:26-28). Never appears in any AI-tell catalog in the research; Microsoft's *human* style guide describes its own brand voice as "crisp and clear" (style-as-code-tooling.md:118). The ban is legitimate as owner preference (it belongs to the self-grading family analyzed in deai §4), but should be annotated as preference-, not evidence-based — sac §9 gap 8 recommends per-entry rationale links for exactly this dispute.
7. **`unpack`** (banned-phrases.yaml:63), **`ecosystem`** (line 70), **`holistic`** (line 72), **`synergy`** (line 71), **`at the end of the day`** (line 64): none appear in either research file. Nearest support is the *existence* of proselint's `industrial_language.corporate_speak` check (style-as-code-tooling.md:73), which is categorical, not phrase-level. `synergy` at **error** is the most exposed — no source ranks it; consider warn or add a provenance note. I state this as absence-of-evidence in these two files, not proof the tells are wrong.
8. **`in today's fast-paced world`** (banned-phrases.yaml:58): the attested antislop forms are "today's digital age" / "in today's digital era" (deai-language-landscape.md:260). Keep the seed entry, but the attested variants (added above) are the grounded ones.

**Re-scoring mechanism issues (not severity, but the research directly bears on them):**

9. **Common-tier words need budgets, not per-hit flags.** `robust` (line 61), `landscape` (line 69), and the new `crucial`/`enhance`/`additionally` entries sit in Kobak's "common but excess" tier, which the research says to "flag only at density, not per-occurrence" (deai-language-landscape.md:113); Hemingway's philosophy independently supports budget semantics for warn-level matches (style-as-code-tooling.md:95). The seed schema has no density/budget mechanism — sac §9 gap 3 flags this. Until it exists, keep these at warn and do not upgrade.
10. **No exceptions mechanism.** `landscape` ("the literal noun" is fine, seed line 69) and the new `associated with` need per-entry `exceptions:`; every surveyed linter has one (Vale `exceptions`, write-good `whitelist`, alex `allow` — style-as-code-tooling.md:166) and the seed lacks it.
11. **Anchored patterns are scope-ambiguous.** `^(great|excellent|good) question` (line 33) and the other `^`-anchored entries anchor to *scope*, which under the planned Vale compile means paragraph/sentence scope must be declared or the anchor means "file start" (style-as-code-tooling.md:49). Applies equally to my new `^`-anchored entries.

**Affirmed by the research (no change):** `delve` error (r=28.0, deai-language-landscape.md:99), `a testament to` error (lines 15, 29), `multifaceted` error (line 111), `nestled` error (lines 18, 262), `not just X, but` warn as the mild form with the em-dash forms now at error (line 42), the entire hedging category (line 154), `without further ado` / `in this section we will` error (line 155), and the summary_inflation set (line 139).

One limitation to note: I could not enumerate other files under `corpus/` or `research/sources/` to check for additional seeds or sources (no Glob/Grep in this session; directory Read fails). If a `corpus/` sibling file already covers formatting or narrative-mode rules, the `format_tells` and `narrative_slop` categories above should be reconciled against it.