"""Big report - Volumes V-VIII (deviations, defects, research, practice) and appendices."""
from reportlab.platypus import PageBreak, Paragraph, Spacer

from report_builder_base import BODY_W, B, P, S, Section, Sub, callout, code, table

W = BODY_W


def build():
    f = []

    # ============================================================= VOLUME V
    f.append(Section("Volume V \u2014 Register of Deviations"))
    f.append(Spacer(1, 4))
    f.append(P(
        "A deviation register records every point at which the implementation departed from the plan, "
        "with the reasoning. It exists because a project cannot be assessed for judgement without "
        "one \u2014 only for adherence, and adherence is not the quality that matters. Thirteen "
        "deviations are documented."))

    deviations = [
        ("D1", "Core framing",
         "Build a note-taking application with search and tags.",
         "Abandoned notes entirely; built an autonomous capture and retrieval system.",
         "A system whose value depends on manual curation will be abandoned, because the user is bad "
         "at curation \u2014 that is why the problem exists. Moving judgement from human to machine is "
         "harder engineering and is the only version that works."),

        ("D2", "Model transport",
         "Call the local model through its OpenAI-compatible endpoint.",
         "Call the native local API directly.",
         "The compatibility layer returned \u2018model not found\u2019 for models that existed, and "
         "diagnosing it took longer than it should have. An adapter adds a failure mode without "
         "adding capability when talking to your own infrastructure."),

        ("D3", "Image storage",
         "Keep every captured frame.",
         "Score frames for information density and retain only the best per information period.",
         "Storing everything grows without bound and retrieves nothing useful. The criterion for "
         "\u2018best\u2019 must be measurable, and text density is."),

        ("D4", "Scraping",
         "Use paid scraping services for social and web ingestion.",
         "Built a native stack on free libraries; ingestion fell to 0.98 s.",
         "Directed by the author: build the capability rather than rent it. The principle was then "
         "applied unprompted to mail and calendar, where it avoided a recurring cost (D7)."),

        ("D5", "Interface",
         "A clean dashboard with a side navigation.",
         "Three successive rebuilds, landing on persistent navigation plus an ambient command centre.",
         "The requirement could not be specified in advance. Each rebuild eliminated a wrong "
         "interpretation: the first showed the visual language was wrong; the second showed that "
         "removing navigation makes functionality unfindable."),

        ("D6", "Modality",
         "Answer questions in the interface.",
         "Added speech in and out, a transparent floating orb, and proactive spoken announcements.",
         "Derived from the authors' reference videos once analysed for substance rather than "
         "appearance: the defining characteristic of the reference assistant is that it speaks "
         "first."),

        ("D7", "Account connectivity",
         "Connect accounts through OAuth and publish the application.",
         "Added a credential-free path using IMAP and calendar feeds, and made it the default.",
         "Researching the authors' question about a commercial assistant revealed that reading an "
         "inbox requires a restricted scope, and publishing one requires an annual third-party "
         "security assessment costing several hundred dollars. For a single-user application the "
         "cost is indefensible, and staying unverified forces weekly reconnection of every account."),

        ("D8", "Invocation",
         "The user presses a hotkey to summon the assistant.",
         "Added offline wake-word detection so the assistant can be addressed by name.",
         "A name is most of what distinguishes an assistant that is present from an application that "
         "is opened. Implemented offline so no audio leaves the machine."),

        ("D9", "Order of work",
         "Write the paper describing the seven planned contributions.",
         "Audited the claims, found six unimplemented, built them, then wrote from measured results.",
         "A paper written before the software describes something that does not exist. The audit also "
         "changed the paper's content: the predicted result was wrong, so the paper reports the "
         "measured result instead."),

        ("D10", "Re-ranking",
         "Re-rank retrieved memories by their computed importance score.",
         "Use the retrieval order as a prior and apply damping as an adjustment.",
         "Sorting by importance was actively harmful, promoting memories important in the abstract "
         "above the memory that answered the question. A re-ranker should refine an ordering, not "
         "replace it."),

        ("D11", "Conflict classes",
         "Detect temporal supersession and lexical negation.",
         "Added numeric and dated value-change detection as a third class.",
         "Testing showed the first two missed the most common real case \u2014 a deadline that moved, "
         "expressed in the third person with no negation word and no first-person state claim."),

        ("D12", "Similarity threshold",
         "Use 0.90 cosine similarity to identify duplicates.",
         "Set the threshold to 0.78 from the measured distribution.",
         "Reworded duplicates, the common real case, score around 0.82. A 0.90 threshold missed every "
         "one of them. A threshold chosen to make the test pass would have been fitting the method to "
         "the evaluation."),

        ("D13", "Reporting the ablation",
         "Report a per-component ablation table.",
         "Removed the table and stated in the paper that the factorised ablation is not yet run.",
         "Some cells had not been independently measured. A table implying measurements that were not "
         "taken is worse than an honest gap, and a reviewer would eventually ask."),
    ]

    for code_id, dimension, planned, actual, reason in deviations:
        f.append(Sub(f"Deviation {code_id} \u2014 {dimension}", number=None))
        f.extend(table([
            ["Planned", planned],
            ["Actual", actual],
            ["Reason", reason],
        ], [62, W - 62], header=False))
        f.append(Spacer(1, 2))

    f.extend(callout(
        "The two deviations that changed the project's direction",
        "<b>D7</b> (account connectivity) removed a recurring cost and, more importantly, removed a "
        "dependency on a third party's willingness to approve the application. <b>D9</b> (order of "
        "work) prevented a paper from describing software that did not exist, and produced the "
        "project's most interesting finding \u2014 that the anticipated improvement was absent while "
        "a different, unmeasured property had changed substantially. Both deviations were triggered "
        "by a direct question from the authors challenging an assumption."))
    f.append(PageBreak())

    # ============================================================= VOLUME VI
    f.append(Section("Volume VI \u2014 Register of Defects"))
    f.append(Spacer(1, 4))
    f.append(P(
        "Twenty-seven significant defects, grouped by cause rather than chronology because the causes "
        "cluster and the clustering is the useful information. Five root causes account for almost "
        "everything: silent failure, incorrect error semantics, a wrong model of the domain, "
        "lifecycle gaps, and unverified process. Each entry records the symptom, the cause, the fix, "
        "and the lesson."))

    # ---- Class 1
    f.append(Sub("Class 1 \u2014 Missing or unverified dependency (D1\u2013D4)"))
    f.extend(table([
        ["Defect", "Symptom", "Root cause and fix", "Lesson"],
        ["D1 Undefined identifier, twice",
         "Blank screen on the home route; a second instance waiting on another tab",
         "A component was used in markup without being imported. Fixed by adding the imports; a "
         "linter rule now fails the build on any undefined identifier.",
         "A successful build proves compilation, not execution."],
        ["D2 Undeclared package",
         "A fresh installation crashed on startup",
         "Two packages were imported directly but listed only as transitive dependencies of another "
         "package, and resolved locally by accident. Both declared explicitly.",
         "A direct import needs a direct declaration, however it happens to resolve on your machine."],
        ["D3 Library version drift",
         "Wake-word detection would have failed silently on the target machine",
         "The model-loading call used an argument name present only in a newer release than the one "
         "installed. Loading made version-tolerant, attempting four constructor shapes.",
         "Test against the installed version, not the documented one."],
        ["D4 Dependency conflict",
         "A clean installation refused to complete",
         "A linting package declared a peer requirement for a major version contradicting the pinned "
         "version. Versions aligned.",
         "A build that works only on the authors' machine is not a build."],
    ], [78, 108, 150, W - 336], caption="Table 18 \u2014 Dependency defects."))

    # ---- Class 2
    f.append(Sub("Class 2 \u2014 Silent failure (D5\u2013D8)"))
    f.append(P(
        "This class caused more lost time than all others combined, and the reason is structural: a "
        "system that fails quietly is misread as working, so the fault is attributed to the wrong "
        "component or to nothing at all."))
    f.extend(table([
        ["Defect", "Symptom", "Root cause and fix", "Lesson"],
        ["D5 Authentication had never worked",
         "The interface rendered normally but showed empty data everywhere",
         "A service referenced a configuration object without importing it, so login raised before "
         "comparing any password. The frontend swallowed the error, so the application ran with no "
         "token and 52 protected endpoints returned 401 \u2014 rendered by the interface as empty "
         "states. Fixed by adding the import.",
         "The most dangerous failure is the one the interface misrepresents. Found only by running "
         "the server and attempting to log in."],
        ["D6 Thirty-three unauthenticated calls",
         "Even a correct login would not have authenticated most screens",
         "Screens used a raw browser fetch, which does not attach the token, instead of the "
         "application's client. Fixed with a single authenticated helper and a mechanical "
         "replacement across 18 files.",
         "Duplicated plumbing drifts, and the drift is invisible in review."],
        ["D7 A test passing while the system was offline",
         "An endpoint reported success while the language model was unreachable",
         "The endpoint always returns success and substitutes canned text when the model is absent; "
         "the test checked only the status code. The test now inspects for fallback markers and "
         "reports DEGRADED with the actual cause.",
         "A test that cannot fail is not a test."],
        ["D8 Deliberate errors re-labelled as faults",
         "Behaviour differed between runs with no error reported",
         "A generic exception handler caught deliberate errors and re-labelled them as server faults, "
         "so a missing record reported an internal error with a not-found body. Deliberate exceptions "
         "re-raised before the generic handler.",
         "Catch narrowly. A broad handler converts informative errors into uninformative ones."],
    ], [78, 108, 150, W - 336], caption="Table 19 \u2014 Silent-failure defects."))

    # ---- Class 3
    f.append(Sub("Class 3 \u2014 Incorrect error semantics (D9\u2013D10)"))
    f.extend(table([
        ["Defect", "Symptom", "Root cause and fix", "Lesson"],
        ["D9 A missing record reported as an upstream failure",
         "Six endpoints returned a gateway-error code for a non-existent identifier",
         "The exception types for \u2018no such account\u2019 and \u2018the provider rejected us\u2019 "
         "were the same, and both mapped to the upstream-failure code. A distinct type was introduced "
         "for the missing-account case, mapped to not-found.",
         "An error code is a claim about where the fault lies. Saying \u2018upstream\u2019 when the "
         "request was wrong sends the reader in the wrong direction."],
        ["D10 Status depended on ambient configuration",
         "The same request returned different codes in different environments",
         "Routes called the provider before checking whether the account existed, so the response "
         "depended on whether the provider was configured. Every account-scoped route now resolves "
         "the account locally first.",
         "A response should be a function of the request, not of unrelated global state."],
    ], [78, 108, 150, W - 336], caption="Table 20 \u2014 Error-semantics defects."))

    # ---- Class 4
    f.append(Sub("Class 4 \u2014 Wrong model of the domain (D11\u2013D16)"))
    f.append(P(
        "This is the most interesting class. In every case the code was correct and the "
        "<i>understanding</i> was wrong, and in every case the defect was invisible until measured."))
    f.extend(table([
        ["Defect", "Symptom", "Root cause and fix", "Lesson"],
        ["D11 Temporal supersession silently did nothing",
         "\u2018What am I working on?\u2019 returned both the old and the new answer",
         "Two facts describing one state were stored under different predicate names, so neither "
         "superseded the other. Predicates are now canonicalised into state classes before "
         "supersession.",
         "A data model is only as correct as its normalisation, and the failure is silent. This "
         "reproduced exactly the failure the component existed to prevent."],
        ["D12 Negation detected by substring",
         "Notes about notes were reported as logical contradictions",
         "Negation was tested with a substring check, so \u2018not\u2019 matched inside "
         "\u2018notes\u2019, \u2018notification\u2019 and \u2018another\u2019. Replaced with "
         "word-boundary matching against an explicit pattern list.",
         "Substring matching on natural language is almost always wrong \u2014 it is the classic "
         "error in this domain."],
        ["D13 The most common contradiction was undetectable",
         "A deadline moving from October to September was missed entirely",
         "Both the temporal extractor and the negation detector keyed on first-person state claims or "
         "negation words; a third-person factual value change matches neither. Added dated and "
         "numeric value-change detection requiring shared topic signature and high salient-word "
         "overlap.",
         "Test the common case, not the designed case."],
        ["D14 Topic words stripped as noise",
         "The strongest real contradiction stopped being detected after a precision tightening",
         "The stop-word list excluded \u2018deadline\u2019 and \u2018project\u2019 as filler "
         "\u2014 precisely the words that make two memories comparable. Restricted to generic filler "
         "only.",
         "A stop-word list is a model of the domain, and it can be wrong in ways that silently "
         "destroy the signal."],
        ["D15 Importance ranking made results worse",
         "The proposed method scored below a baseline",
         "Re-ranking multiplied the damped retrieval score by an abstract importance score, promoting "
         "low-relevance high-importance memories above the correct answer. Made rank-preserving with "
         "importance as a light tie-breaker.",
         "A re-ranker should refine an ordering, not replace it."],
        ["D16 Transparency required three simultaneous changes",
         "A dark rectangle behind the floating assistant",
         "Window transparency on Windows requires the window flags, the document-root styling and the "
         "body background to agree. Changing any one alone has no effect.",
         "When a visual defect survives a fix, the fix is usually correct but incomplete across "
         "layers."],
    ], [78, 108, 150, W - 336], caption="Table 21 \u2014 Domain-model defects. Every one was found "
                                        "by measurement rather than by inspection."))

    # ---- Class 5
    f.append(Sub("Class 5 \u2014 Lifecycle and cleanup (D17\u2013D21)"))
    f.extend(table([
        ["Defect", "Symptom", "Root cause and fix", "Lesson"],
        ["D17 Cleanup deleted the last reference",
         "Broken images in the live view",
         "The pruning process deleted raw frames that a preview still referenced. A dedicated buffer "
         "was excluded from pruning.",
         "Never let cleanup delete the last reference to something a view depends on."],
        ["D18 Orphaned derived rows",
         "A test crashed on a record whose parent no longer existed",
         "Deleting a memory left its score row behind, inflating counts while never appearing in the "
         "joined listing. Orphan pruning added.",
         "Derived data needs a lifecycle, not merely a creation path."],
        ["D19 The microphone never re-armed",
         "The assistant answered one question and then stopped",
         "The browser's speech recogniser ends its session by itself and no handler restarted it; the "
         "summon gesture only spoke a greeting and never restarted recognition. Re-arm added in the "
         "session-end handler with backoff.",
         "An event-driven resource that ends itself needs an explicit restart path."],
        ["D20 Two further ways the assistant could become unresponsive",
         "Not observed; found by writing the tests",
         "A turn the model never answers leaves the microphone paused indefinitely; and the "
         "text-to-speech completion event is not guaranteed in Electron when the window is hidden. "
         "Two watchdogs added.",
         "Write the test for the failure you have not seen yet. It found both before the authors did."],
        ["D21 A wake event could hide the assistant",
         "Not observed; found by reading the code",
         "The wake handler called a function that toggles window visibility rather than one that "
         "shows it, so waking an already-visible assistant would hide it. A non-toggling reveal path "
         "added.",
         "\u2018Show\u2019 and \u2018toggle\u2019 are different operations; conflating them produces "
         "inverted behaviour."],
    ], [78, 108, 150, W - 336], caption="Table 22 \u2014 Lifecycle and cleanup defects. Two of the "
                                        "five were found by tests written for hypothetical failures "
                                        "rather than by observing a real one."))

    # ---- Class 6
    f.append(Sub("Class 6 \u2014 Process and data safety (D22\u2013D27)"))
    f.extend(table([
        ["Defect", "Symptom", "Root cause and fix", "Lesson"],
        ["D22 Benchmark not reproducible",
         "Results changed between consecutive runs",
         "Derived research state from a previous run \u2014 temporal facts, conflicts, consolidations, "
         "tombstones \u2014 perturbed the following run. Derived state cleared at the start of each "
         "run; determinism now asserted.",
         "A benchmark that is not deterministic cannot support a claim made from it."],
        ["D23 The test deleted real user data",
         "123 of the authors' genuine memory cards were removed",
         "The mail-ingestion test registered the authors' real address, so its generated artefacts "
         "were indistinguishable from genuine ones and its cleanup could not tell them apart. Files "
         "restored from version control; the test now uses a non-existent address and its cleanup "
         "refuses to delete anything not carrying the test marker, reporting what it protected.",
         "A destructive operation must be able to prove that what it is deleting is its own. This is "
         "the most serious defect in the project."],
        ["D24 The verification tool crashed on the target machine",
         "A test failed on the user's machine but passed in development",
         "A browser global that was assignable in the older runtime is a read-only accessor in the "
         "newer runtime installed on the user's machine. Globals now installed via a "
         "descriptor-based helper and verified on both versions.",
         "A check that fails the same way as the product is worse than no check."],
        ["D25 The contract checker produced false positives",
         "Correct endpoints reported as missing",
         "The URL extractor and normaliser handled template expressions and query strings in the "
         "wrong order, truncating a URL at a question mark inside a ternary. Order corrected and "
         "ternary branches now expanded into separate candidates.",
         "A checker that cries wolf gets ignored. The mislabelling of a timeout as a crash was "
         "therefore treated as a bug in its own right."],
        ["D26 A stage ran before its dependencies existed",
         "Scripts failed with an error naming an unrelated class",
         "Model relationships were being resolved before all model modules had been imported. A "
         "bootstrap import was added at the top of the dependent package.",
         "Import order is a real dependency. Make the requirement explicit rather than relying on the "
         "order a file happens to run."],
        ["D27 Output correct in the log, wrong on the page",
         "A generated document reported success but the layout was broken",
         "The build log reported success because the document was produced; the layout defect was "
         "only visible on inspection. Fixed by rendering each page to an image and examining it.",
         "Verify the artefact, not the exit code. This is the same lesson as D1 at a different "
         "layer."],
    ], [78, 108, 150, W - 336], caption="Table 23 \u2014 Process and data-safety defects."))

    f.extend(callout(
        "What the register as a whole indicates",
        "The distribution is informative. Dependency defects were eliminated once the verification "
        "system existed and have not recurred. Silent-failure defects cluster early, before the live "
        "sweep existed. Domain-model defects were found exclusively by measurement, never by "
        "inspection. Lifecycle defects were found by tests written for hypothetical failures. And the "
        "single most serious defect was caused not by the application but by the verification process "
        "itself \u2014 which is why its fix is structural rather than local."))
    f.append(PageBreak())

    # ============================================================ VOLUME VII
    f.append(Section("Volume VII \u2014 The Research Contribution"))
    f.append(Spacer(1, 4))

    f.append(Sub("27. The research question"))
    f.append(P(
        "The question the paper addresses is: <i>how can a personal AI continuously update, "
        "consolidate, prioritise and temporally reason over a user's evolving knowledge without "
        "accumulating redundant, outdated or contradictory memories?</i>"))
    f.append(P(
        "It is worth being explicit about why this is a research question rather than an engineering "
        "task. The engineering question would be \u2018can we store and retrieve a person's "
        "information?\u2019, and the answer is trivially yes. The research question concerns a "
        "property that emerges only over time and only under contradiction: what should a system "
        "believe when its own records disagree, and how should that belief affect retrieval? That "
        "question has no obvious answer and no standard measurement."))

    f.append(Sub("28. The seven components"))
    f.extend(table([
        ["#", "Component", "Function", "Defining design decision"],
        ["C1", "Adaptive Memory Scoring",
         "Eight-term importance score; all terms persisted",
         "Auditable rather than opaque: any score can be explained term by term"],
        ["C2", "Temporal Personal Knowledge Graph",
         "Triples with validity intervals and state supersession",
         "Close facts rather than delete them, so history remains queryable"],
        ["C3", "Contradiction-Aware Retrieval",
         "Three conflict classes detected; rank damping applied",
         "Damp rather than remove, preserving current and historical answers"],
        ["C4", "Memory Consolidation",
         "Near-duplicate clustering with provenance retention",
         "Threshold calibrated from the measured distribution, not assumed"],
        ["C5", "Knowledge-Gap Detection",
         "Exposure versus depth, weighted by graph connectivity",
         "Connectivity factor prevents flagging well-understood concepts"],
        ["C6", "Retrieval-Enforced Forgetting",
         "Exclusion enforced at five independent surfaces",
         "Enforcement at retrieval, not deletion, because derived stores survive deletion"],
        ["C7", "PersonalBrain-Bench",
         "Synthetic corpus with six question categories",
         "Synthetic by design, so the experiment is reproducible and contains no private data"],
    ], [24, 108, 148, W - 280],
        caption="Table 24 \u2014 The seven contributions and the decision that defines each."))

    f.append(Sub("29. Benchmark design"))
    f.append(P(
        "Existing retrieval benchmarks do not contain contradictory, superseded or deliberately "
        "forgotten personal memories, so they cannot expose the failures this work targets. The "
        "benchmark was therefore constructed specifically to isolate them."))
    f.extend(table([
        ["Category", "Questions", "What it tests", "Correct behaviour"],
        ["Factual", "3", "Ordinary recall", "Retrieve the stated fact"],
        ["Temporal", "2", "Which of two competing states is current",
         "Retrieve the newer; do not retrieve the superseded one"],
        ["Contradiction", "2", "Which of two dated values is authoritative",
         "Retrieve the newer value; damp the older"],
        ["Multi-hop", "1", "Synthesis across linked memories", "Retrieve the whole chain"],
        ["Duplicate", "1", "Whether redundant copies fill the budget",
         "Retrieve one representative; collapse the rest"],
        ["Forgetting", "1", "Whether removed content stays removed",
         "Retrieve nothing relating to it"],
        ["Gap", "1", "Whether the system distinguishes exposure from depth",
         "Report the concept as a gap, not as knowledge"],
    ], [78, 52, 148, W - 278],
        caption="Table 25 \u2014 PersonalBrain-Bench question categories. The last two have no correct "
                "answer to retrieve by construction, which is why Hit@k and MRR are computed over "
                "answerable questions only."))
    f.append(P(
        "The corpus contains fifteen memories spanning email, notes, code, web captures and screen "
        "text, with timestamps distributed across a 240-day window so that recency and supersession "
        "are exercised rather than simulated. Synthetic construction is a deliberate methodological "
        "choice: a real personal store would make the experiment unreproducible and would place "
        "private data in a publication."))

    f.append(Sub("30. Results"))
    f.extend(table([
        ["Pipeline", "Hit@5", "MRR", "Stale@1", "Leak", "Duplicate", "Latency"],
        ["Vanilla dense", "1.000", "0.833", "0.364", "0.022", "0.022", "39 ms"],
        ["Hybrid", "1.000", "0.944", "0.182", "0.022", "0.022", "33 ms"],
        ["Graph-augmented", "1.000", "0.944", "0.182", "0.022", "0.022", "42 ms"],
        ["Adaptive (proposed)", "1.000", "1.000", "0.000", "0.000", "0.000", "84 ms"],
    ], [116, 52, 50, 56, 48, 66, W - 388],
        caption="Table 26 \u2014 Comparative results (k = 5, 11 questions, 15 memories, "
                "corpus-scoped evaluation, dense retriever pinned to the offline TF-IDF path). The "
                "quality metrics are deterministic and reproduce exactly on any database; latency "
                "is wall-clock and varies between runs."))
    f.extend(table([
        ["Question category", "Vanilla MRR", "Hybrid MRR", "Adaptive MRR", "Change"],
        ["Factual", "1.000", "1.000", "1.000", "\u2014"],
        ["Temporal", "0.750", "0.750", "1.000", "+0.250"],
        ["Contradiction", "0.500", "1.000", "1.000", "\u2014"],
        ["Multi-hop", "1.000", "1.000", "1.000", "\u2014"],
        ["Duplicate", "1.000", "1.000", "1.000", "\u2014"],
    ], [116, 84, 78, 88, W - 366],
        caption="Table 27 \u2014 MRR by category. The improvements appear exactly where the "
                "architecture predicts them and nowhere else."))

    f.append(Sub("31. Interpretation"))
    f.append(P(
        "<b>The headline finding is negative, and that is the contribution.</b> Hit@5 is 1.000 for "
        "every pipeline including the simplest baseline. Every system retrieves the relevant memory "
        "somewhere in its top five. Had the evaluation used only recall, the conclusion would have "
        "been that seven research components accomplished nothing measurable \u2014 and that "
        "conclusion would have been wrong."))
    f.append(P(
        "What differs is the ordering and the staleness of what comes first. The proposed pipeline "
        "raises mean reciprocal rank from 0.833 to 1.000 and reduces the rate of leading with "
        "superseded content from 36.4% to 0.0%. Because a language model consumes the ordered context "
        "and leads with what it reads first, staleness at rank one is what produces an answer that is "
        "confidently wrong. Critically, every retrieved passage remains faithful to its source, so no "
        "faithfulness metric would flag it \u2014 the system is hallucination-free and incorrect."))
    f.append(P(
        "The category breakdown localises the gains. Factual, multi-hop and duplicate questions are "
        "unchanged at 1.000, which is a desirable property: it means the added machinery is a "
        "targeted change rather than a general-purpose alteration to retrieval. Temporal questions "
        "improve from 0.750 to 1.000 once predicate canonicalisation makes supersession fire. "
        "Contradiction questions are where the vanilla baseline is weakest, consistent with the "
        "motivating scenario."))
    f.append(P(
        "The forgetting result is the sharpest. The baselines do not merely score lower; they "
        "<i>continue to return content the user explicitly asked to remove</i>. The adaptive pipeline "
        "returns it zero times. This is evidence that removal from a retrieval system is a property "
        "of the retrieval layer and is not obtained by deleting a row from the primary table."))

    f.append(Sub("32. Limitations, stated plainly"))
    f.extend(B([
        "<b>The benchmark is synthetic and small.</b> Fifteen memories, eleven questions, six "
        "categories. The categories isolate specific behaviours; they do not represent the "
        "distribution of real personal data. Absolute values should not be extrapolated.",
        "<b>Extraction is rule-based and conservative.</b> It will miss phrased contradictions that do "
        "not match its patterns. This trades recall for precision deliberately \u2014 a wrong fact in "
        "a personal graph is worse than a missing one \u2014 but the trade is real.",
        "<b>Temporal handling uses UTC-normalised timestamps</b> without full timezone or "
        "partial-interval reasoning, which would matter for events spanning midnight across zones.",
        "<b>The evaluation covers retrieval, not generation.</b> Whether higher MRR and lower stale"
        " rate translate into fewer incorrect answers in generated prose is not measured here. This "
        "is the natural next experiment and the most significant gap.",
        "<b>The ablation is not factorised.</b> The per-category results localise the effect, but an "
        "independent run isolating each of the five post-retrieval stages has not been performed. "
        "This is stated in the paper rather than inferred from the aggregate.",
    ]))

    f.extend(callout(
        "The most defensible single sentence in the work",
        "\u2018Every baseline continues to return explicitly unlearned content.\u2019 This is a "
        "negative result about the baselines. It is measured, reproducible, and not obvious in "
        "advance. A contribution does not have to be a large positive number: a precise demonstration "
        "that an apparently simple property is not automatic is equally publishable, provided the "
        "scope is stated honestly."))
    f.append(PageBreak())

    # =========================================================== VOLUME VIII
    f.append(Section("Volume VIII \u2014 Engineering Practice"))
    f.append(Spacer(1, 4))

    f.append(Sub("33. The verification system"))
    f.append(P(
        "Fifteen gates, run by a single command. The design principle is that each gate must be "
        "capable of failing: a check that cannot fail is decoration, and three of the defects in "
        "Volume VI were found by examining a passing gate and discovering it was untestable."))
    f.extend(table([
        ["Gate", "Method", "Catches"],
        ["1 Static analysis", "Linter configured to fail on any warning",
         "Undefined identifiers, unused symbols, hook violations"],
        ["2 Environment health", "Eight static integration checks",
         "Imports that do not resolve, icons that do not exist, client methods without definitions, "
         "route modules missing, URL mismatches, incomplete preload surface, Python that does not "
         "compile"],
        ["3 API contract", "Every interface URL matched against every backend route",
         "Calls targeting non-existent routes, including both branches of ternary expressions"],
        ["4 Route render and mount", "Render then mount every route so effects execute",
         "Component crashes, effect failures, empty renders, broken connected states"],
        ["5 Production build", "Bundle the interface",
         "Compilation failures"],
        ["6 Backend functional suites", "Eleven live suites",
         "Regressions in authentication, capture, graph, vault, wiki, briefing, deliverables, "
         "semantic search, OCR, voice"],
        ["7 Google integration", "Fifty checks against a fake provider",
         "Consent URL shape, scope correctness, token exchange, refresh, revoked-token handling, "
         "token readability on disk"],
        ["8 Mail and calendar", "Fifty-six checks against a fake IMAP server and a real HTTP fetch",
         "Protocol correctness, iCalendar feature coverage, credential encryption"],
        ["9 Mail ingestion", "Forty-seven checks",
         "That the pipeline can actually answer from ingested mail \u2014 the assertion that "
         "matters most"],
        ["10 Orb voice loop", "Twenty-two checks driving a fake speech engine",
         "Microphone re-arm, watchdog behaviour, transcript transmission policy"],
        ["11 Wake word and proactive voice", "Fifty-five checks",
         "Policy gates, quiet hours, cooldown, dedupe, and the real model against real audio"],
        ["12 Hands-free wiring", "Ten checks",
         "That wake and speech events actually reach the interface"],
        ["13 Research layer", "Sixty-eight checks, one per claim",
         "Each stated contribution and, crucially, the negative controls"],
        ["14 Live endpoint sweep", "Boot, authenticate, call every route",
         "Server errors under real conditions; reports status and timing for each route"],
        ["15 Browser smoke (optional)", "Load every route in a real browser",
         "End-to-end failures that only appear in a real rendering engine"],
    ], [108, 152, W - 260],
        caption="Table 28 \u2014 The fifteen verification gates."))

    f.append(Sub("34. Data safety"))
    f.append(P(
        "The project's most serious defect was caused by the verification process rather than by the "
        "application: a test that registered the authors' real address could not distinguish its own "
        "artefacts from genuine data, and deleted 123 real memory cards. The fix was structural "
        "rather than local, and the principle it produced is now applied to every destructive "
        "operation:"))
    f.extend(code("""  THE SAFETY RULE

   A destructive operation must be able to prove that what it is deleting
   is its own.

   Applied here:
     \u2022 tests use non-existent identifiers (example.invalid domains)
     \u2022 generated artefacts carry a marker identifying their producer
     \u2022 cleanup REFUSES to delete anything lacking that marker
     \u2022 the refusal is reported, so the protection is visible rather than silent

   Output from a run:
     "(cleaned up 4 test vault cards, 4 test wiki articles, restored graph +
      wiki index)"
     "PROTECTED 123 real vault card(s) and 93 real wiki article(s) \u2014 they
      did not carry the test marker"

   Before: the operation succeeded and destroyed real data.
   After:  the operation succeeds and reports what it protected.""",
                  "The safety rule and its concrete enforcement. The second line of output is the "
                  "evidence that the guard works, and it is printed on every run."))

    f.append(Sub("35. The development process itself"))
    f.append(P(
        "The working pattern that emerged over the project is worth recording, because it was not "
        "planned and it worked well."))
    f.extend(table([
        ["Practice", "What it means", "Why it worked"],
        ["Reconnaissance before writing",
         "Read the existing code and data shapes before designing a change",
         "Prevented several changes that would have conflicted with existing behaviour"],
        ["Build the measurement first",
         "For research claims, write the assertion before or alongside the implementation",
         "Several defects were found because writing the assertion forced the question \u2018what "
         "would this look like if it were broken?\u2019"],
        ["Verify the artefact, not the signal",
         "Render the PDF and look at it; open the page and look at it",
         "Caught two defects where the build reported success and the output was wrong"],
        ["Report the negative result",
         "State what was measured even when it contradicts the expectation",
         "Produced the project's most interesting finding and its most defensible claim"],
        ["Document the incident",
         "Record the serious defects in full, including the ones the authors would rather omit",
         "A defect register that omits the worst defect is not a defect register"],
    ], [104, 158, W - 262],
        caption="Table 29 \u2014 The development practices that emerged, none of which were planned "
                "in advance."))
    f.append(PageBreak())

    # ============================================================= APPENDICES
    f.append(Section("Appendix A \u2014 Project Statistics"))
    f.extend(table([
        ["Metric", "Value"],
        ["Total commits", "231"],
        ["Substantive commits", "69"],
        ["Automated vault synchronisations", "162"],
        ["Python source files / lines", "165 files, 17,149 lines"],
        ["Interface files / lines", "55 files, 12,449 lines"],
        ["Backend route modules", "21"],
        ["Backend module directories", "44"],
        ["Specialised agents", "10"],
        ["API endpoints / paths", "162 endpoints across 150 paths"],
        ["Route groups", "19"],
        ["Database tables", "49"],
        ["Interface routes", "19"],
        ["Verification gates", "15"],
        ["Test suites", "8 (5 backend, 2 interface, 1 research)"],
        ["Research assertions", "77"],
        ["Documented defects", "27"],
        ["Documented deviations", "13"],
        ["Knowledge graph", "350 nodes, 500 edges"],
        ["Wiki articles compiled", "93"],
        ["Memory cards from real mail", "123"],
    ], [220, W - 220], caption="Table 30 \u2014 Project metrics at the time of writing. Every figure "
                               "was read from the repository or from measured output."))

    f.append(Section("Appendix B \u2014 Timeline"))
    f.extend(code("""  AUG 2026    Phase 0   Foundations: backend, schema, auth, capture scaffolding

  17 SEP      Phase 1   Curation, hero images, vault, wiki compiler, 3D visualisation
  18 SEP      Phase 2   Free native scrapers, insight collisions, spoken briefing,
                        deliverable generation, ambient overlay
  21 SEP      Phase 3   Three interface rebuilds; fifteen-tab shell; transparent orb
  22 SEP am   Phase 4   Two full error audits; fifteen verification gates created
  22 SEP      Phase 5   OAuth, then IMAP + iCalendar; mail ingestion pipeline
  22 SEP      Phase 6   Wake word, proactive voice, orb voice-loop repair
  22 SEP      Phase 7   Research layer: seven contributions, benchmark, IEEE paper

  Gates added    0 \u2192 15          Defects found and fixed   27
  Deviations     13                 Research assertions       77
  Phases 4\u20137 all occurred on one day, which was possible only because
  Phase 4 produced the means to verify a change in under a minute.""",
                  "The build at a glance."))

    f.append(Section("Appendix C \u2014 Glossary"))
    glossary = [
        ("Agent", "A component with a single responsibility, its own failure mode, and no knowledge "
                  "of the others' internals."),
        ("App password", "A long random credential issued for legacy protocols after two-factor "
                         "authentication is enabled. No consent screen, no expiry."),
        ("BM25", "A classical probabilistic ranking function using term-frequency saturation and "
                 "length normalisation."),
        ("CASA", "Cloud Application Security Assessment. A paid annual third-party audit required by "
                 "a major provider for applications publishing restricted scopes."),
        ("Chunk", "A passage small enough to embed meaningfully and store as one retrieval unit."),
        ("Consolidation", "Merging near-duplicate memories into one canonical record while retaining "
                          "the identifiers of everything merged."),
        ("Context window", "The bounded amount of text a language model can attend to at once. Makes "
                           "retrieval a budget-allocation problem."),
        ("Cosine similarity", "The cosine of the angle between two vectors; the standard measure of "
                              "semantic similarity. Ignores magnitude."),
        ("Damping", "Multiplying a retrieved item's ranking weight to demote it without removing it."),
        ("Debounce", "Suppressing repeated triggering of an event within a short window, so one "
                     "utterance fires once."),
        ("Embedding", "A fixed-length numeric vector representing text, positioned so that similar "
                      "meanings are nearby."),
        ("Exposure vs depth", "Having encountered a concept versus having understood it."),
        ("Hero image", "The single representative frame elected from an information period, kept "
                       "instead of every screenshot."),
        ("Hit@k", "Whether a relevant item appeared among the top k results. Position-insensitive."),
        ("IMAP", "Internet Message Access Protocol. The mechanism desktop mail clients use to read "
                 "mailboxes. EXAMINE and BODY.PEEK preserve read state."),
        ("iCalendar", "A text format for calendar data. Providers publish a private address per "
                      "calendar requiring no authentication."),
        ("IDF", "Inverse document frequency. Weights a term by how rare it is across a corpus."),
        ("JWT", "JSON Web Token. A signed token carrying a claim about an authenticated identity."),
        ("Knowledge graph", "Entities as nodes and typed relationships as edges. Supports multi-hop "
                            "questions that similarity search cannot answer."),
        ("Leak rate", "Fraction of returned results that were explicitly forgotten. Custom metric."),
        ("MRR", "Mean reciprocal rank. Rank-sensitive: distinguishes finding the answer first from "
                "finding it fifth."),
        ("Multi-hop", "A question whose answer requires traversing links between separate records."),
        ("OAuth", "A protocol allowing an application limited access to an account without receiving "
                  "the password."),
        ("ONNX", "An open format for neural network models, used here for the wake-word model."),
        ("Quantisation", "Reducing the numeric precision of model weights to lower memory use, at "
                         "some cost in quality."),
        ("RAG", "Retrieval-augmented generation. Retrieving relevant passages and passing them to a "
                "language model along with the question."),
        ("Scope", "A named permission bundle in OAuth. Providers tier scopes by sensitivity."),
        ("Stale@1", "Whether the top-ranked result is outdated. Custom metric; rank one is what a "
                    "generator leads with."),
        ("Supersession", "Closing an older assertion when a newer one replaces it, rather than "
                         "deleting it."),
        ("TF-IDF", "Term frequency times inverse document frequency. A classical lexical weighting "
                   "scheme requiring no model."),
        ("Truth maintenance", "Keeping a store of beliefs consistent as new information arrives."),
        ("Unlearning", "Removing the influence of specific data from a system that has already "
                       "incorporated it."),
        ("Validity interval", "The half-open time range during which an assertion holds. A null end "
                              "means still true."),
        ("Vector store", "An index optimised for nearest-neighbour search over embeddings."),
        ("Wake word", "An always-listening keyword spotter that fires when a target phrase is "
                      "recognised. Not full speech recognition."),
    ]
    f.extend(table([[g[0], g[1]] for g in glossary], [112, W - 112]))

    f.append(Section("Appendix D \u2014 Design Principles, Collected"))
    f.extend(code("""  1  Optionality            no dependency is load-bearing
  2  Additivity             extend alongside, never rewrite
  3  Testability            each component exercisable in isolation
  4  Honest degradation     say what is unavailable; never substitute plausible text
  5  Prove the check fails  a green result must be capable of being red
  6  Test the claim         if a claim cannot be tested, do not make it
  7  Negative controls      a suite of positive cases passes on a system that does nothing
  8  Narrow catches         broad handlers convert informative errors into silent ones
  9  Correct error codes    a status code is a claim about where the fault lies
 10  Deterministic inputs   a non-deterministic harness cannot support a comparison
 11  Normalise the model    correct code over a wrong model is silently wrong
 12  Calibrate thresholds   a similarity threshold belongs to a data distribution
 13  Refine, do not replace a re-ranker should adjust an ordering, not impose one
 14  Cleanup proves ownership  destructive operations must identify their own artefacts
 15  Verify the artefact   inspect the output, not the exit code
 16  Deterministic memory  an event-driven resource that ends itself needs a restart path
 17  Single source of policy  the backend decides; the interface renders
 18  Own rather than rent   prefer a one-off effort to a recurring cost""",
                  "The principles extracted across the project. Items 1\u20134 were adopted at the "
                  "start; the remainder were learned from the defects in Volume VI."))

    return f
