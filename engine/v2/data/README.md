# RWS knowledge layer

`rws_knowledge.json` is a generated, versioned index for all 78 Rider-Waite-Smith cards. It separates four things that the v1 files mixed together:

1. card identity and deck structure
2. observable visual inventory
3. primary-source links
4. provisional modern interpretation

Every card links to its relevant chapter in A. E. Waite's *The Pictorial Key to the Tarot*. Major Arcana cards additionally link to Waite's shared divinatory-meaning section. A machine-imported candidate transcription now supplies description, upright meaning, and reversed meaning for every card where Waite actually provided one. The image source points to Wikimedia Commons as a candidate collection only; a file is not cleared for product use until its individual file page has been reviewed.

The source registry also records a Wikimedia Commons scan and its SHA-256 digest for offline verification. The 73MB PDF is intentionally not committed.

The generated records deliberately exclude v1 `jungian_mapping`, numerical emotional scores, and `complex_signals`. Those fields are analysis priors, not card knowledge.

## Current status

- 78/78 records migrated and source-linked
- 78/78 Waite description and upright candidates machine-transcribed
- 77/78 Waite reversed candidates machine-transcribed; Waite supplies no separate reversed entry for the Two of Cups, which is represented as `null` rather than invented
- 78/78 identities checked automatically against the v1 deck
- field-level review still pending for Waite text, visual inventory, and modern interpretation
- individual production image assets are not yet selected
- runtime status is `shadow_read_only`; current prompts do not consume this database

Regenerate deterministically after a v1 source correction:

```bash
python -m engine.v2.build_knowledge
```

The one-time source ingestion tool accepts a local cache of the public-domain transcription pages:

```bash
python -m engine.v2.ingest_waite --source-dir /tmp/liminal_waite_pages
```

Activation is a later, explicit change. It must preserve the canonical/situated input boundary, update the prompt lock, pass all regression tests, and then undergo human evaluation. A data edit alone must not change the accepted alpha prompts.
