# respeak references

The sources behind each design concept, fetched and read during the research runs (2026-08-31); the distilled studies live in `research/sources/`.

**Why swarms drift into shorthand (linguistics of convention)**

- Clark & Wilkes-Gibbs, *Referring as a collaborative process*: conceptual
  pacts; 40 words become "the skater" in six rounds.
  <https://en.wikipedia.org/wiki/Conceptual_pact>
- Clark & Brennan, grounding and common ground: why the reader's decoding
  effort counts in the cost. <https://en.wikipedia.org/wiki/Grounding_in_communication>
- Pickering & Garrod, interactive alignment: entrainment is automatic, so
  drift needs no decision. <https://en.wikipedia.org/wiki/Interactive_alignment>
- Garrod et al., experimental semiotics: evolved signs go opaque to
  outsiders. <https://en.wikipedia.org/wiki/Experimental_semiotics>
- Zipf's law of abbreviation: frequent forms shorten.
  <https://en.wikipedia.org/wiki/Brevity_law>
- Piantadosi, Tily & Gibson (PNAS 2011): word length tracks information
  content; never compress high-surprisal content.
  <https://www.pnas.org/doi/10.1073/pnas.1012551108>

**Governed shorthand in the wild (the lexicon model)**

- Multiservice tactical brevity codes: the governed-dictionary pattern.
  <https://en.wikipedia.org/wiki/Multiservice_tactical_brevity_code>
- Ham radio Q codes: central ratification and deprecation.
  <https://en.wikipedia.org/wiki/Q_code>
- Medical abbreviation bans: compression rolled back after it caused harm;
  the model for `never_compress`.
  <https://en.wikipedia.org/wiki/List_of_abbreviations_used_in_medical_prescriptions>

**Machine-lane prior art (compression and agent communication)**

- Lewis et al. 2017, the FAIR negotiation agents: "no reward to sticking to
  English"; legibility must be a reward channel.
  <https://arxiv.org/abs/1706.05125>
- Agora protocol (Oxford): frequency-tiered agent communication, the
  lexicon's economics. <https://arxiv.org/abs/2410.11905>
- LLMLingua / LLMLingua-2: per-message statistical compression and its
  legibility cost. <https://github.com/microsoft/LLMLingua>,
  <https://arxiv.org/abs/2310.05736>, <https://arxiv.org/abs/2403.12968>
- TOON: 42.6% fewer tokens than JSON at higher accuracy, under a versioned
  spec; the governance template. <https://github.com/toon-format/toon>
- SynthLang: an evolving glyph lexicon, with no legibility signal.
  <https://github.com/ruvnet/SynthLang>
- DroidSpeak: the sub-linguistic extreme respeak argues against.
  <https://arxiv.org/abs/2411.02820>
- GibberLink: the announced mode-switch precedent.
  <https://github.com/PennyroyalTea/gibberlink>
- Caveman: token-efficiency proxy; "verified savings" as the burden of
  proof. <https://caveman.so/>

**The AI-tell corpus (evidence for the banned phrases)**

- Wikipedia, *Signs of AI writing*: the editor-maintained tell catalog.
  <https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing>
- Kobak et al., excess vocabulary in LLM-era text: effect sizes for `delve`
  and family. <https://arxiv.org/abs/2406.07016>
- AntiSlop sampler: generation-time slop suppression and its phrase corpus.
  <https://github.com/sam-paech/antislop-sampler>

**Style as data (the config and CI path)**

- Vale: styles as versioned YAML packages, the compile target.
  <https://vale.sh/>
- Mailchimp content style guide: voice constant, tone varies by reader
  state. <https://styleguide.mailchimp.com/>
- Google developer documentation style guide.
  <https://developers.google.com/style>
- Diátaxis: document modes keyed to reader need, the analogy for
  eli5/bluf/technical. <https://diataxis.fr/>

**Communication standards (the mode contracts)**

- US federal plain-language guidelines: verbs over nominalizations, reader-
  first structure. <https://www.plainlanguage.gov/guidelines/>
- GOV.UK style guide: "cannot, not can't"; numbered steps for processes.
  <https://www.gov.uk/guidance/style-guide/a-to-z-of-gov-uk-style>
- ASD-STE100 Simplified Technical English: the sentence caps.
  <https://www.asd-ste100.org/>
- BLUF (bottom line up front): answer first, and the delete test.
  <https://en.wikipedia.org/wiki/BLUF_(communication)>
- Barbara Minto, the Pyramid Principle: grouped, MECE, answer-first
  argument. <https://en.wikipedia.org/wiki/Barbara_Minto>
- Radical Candor (Kim Scott): the checkable feedback switches.
  <https://www.radicalcandor.com/blog/what-is-radical-candor/>
- Crucial Conversations: facts before stories; contrasting statements.
  <https://cruciallearning.com/crucial-conversations-book/>

**The substrate (Anthropic engineering + Claude Code)**

- *Writing effective tools for agents*: the ResponseFormat precedent for
  mode parameters.
  <https://www.anthropic.com/engineering/writing-tools-for-agents>
- *Effective context engineering for AI agents*: the attention-budget
  argument for the machine lane.
  <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>
- *Effective harnesses for long-running agents*: structured registries
  resist drift; the lexicon's file-format lesson.
  <https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents>
- Claude Code docs (skills, subagents, hooks, plugins): the integration
  surfaces. <https://code.claude.com/docs>
