# libs - the pattern library repository

Black box. This folder is the factory: the generators that turn a specification into code.
It lives only in this private repository and on the engine host. It is never shipped to a
client, never exposed through the API, never shared with a partner. Customers receive output.

## Layout

- `taxonomy.yaml` - the ten categories and fifty-eight slots of the filing, the 80/20 core set, and the pack list.
- `catalog/*.yaml` - the exhaustive inventories, enumerated from the installed package versions
  (React core, TypeScript, Next.js, Amplify UI and connected packages, Material Web, Firebase,
  React Native and Expo plus the field-operations patterns). Every entry carries a category letter,
  a tier (`core` = used on most screens, `extended` = the rest) and, when a generator exists, the
  pattern id and `status: generated`.
- `jsx.py` - the shared helpers every generator uses: escaped text, attributes, required-property checks.
- `registry.py` - loads the catalogs, validates them, and registers packs into a `PatternLibrary`.
- `packs/<pack>/patterns.py` - one pack per target. Each exposes `PATTERNS`, `TYPE_MAPPING`,
  `SAMPLES` (sample props for the golden test) and `register(library)`.
- `tests/` - catalog validity, every pattern renders from its sample, golden hashes per pack.

## Rules

1. Patterns are registered, never edited into the engine. A new component is a new pattern with
   a new id; an existing id never changes its output without a pattern library version bump.
2. Every generator is a pure function of its props: no clock, no randomness, no environment,
   no network. Text goes through `jsx.t()` so content can never break a file.
3. Every pattern has a sample in `SAMPLES`; the golden test records the hash of every sample
   render per pack and fails on any drift.
4. A catalog entry becomes `status: generated` only when its pattern id resolves in the registry.
5. Nothing in this folder names a customer, a partner, or a filing number.

## Growing the library

Add the component to its catalog first (tier, category). Write the generator in the pack.
Add the sample. Run `python -m unittest discover -s libs/tests`. Record the new golden hash.
Bump `PATTERN_LIBRARY_VERSION` when the registered set changes.
