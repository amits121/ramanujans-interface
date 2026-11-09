# Proven components

The components the founder's production applications actually use, kept apart from the
exhaustive catalogs in `libs/catalog/`. A catalog lists everything a package exports; a
proven register lists what has run in production, where, in which package version, and
whether it still exists and is still supported upstream.

- `amplify-ui-react.yaml` - the component-framework UI package: used extensively by the
  production web application (19 components across 26 files on 2026-11-09).
- `firebase.yaml` - the Firebase web SDK: catalogued and generated for the firebase target,
  but no production usage was found in any of the four application trees on 2026-11-09.
  Status: catalogued, not proven.
- `react-native-expo.yaml` - React Native, Expo and the field-operations modules the field
  application uses in production.

## The monthly check

On the first of every month (and on demand) `scripts/verify_components.py`:

1. scans the named source trees for every import of the registered packages, so the
   registers reflect real usage, not memory;
2. reads the installed package versions and enumerates the runtime exports of each package
   through Node, the ground truth for "does this component still exist";
3. marks deprecations from `@deprecated` tags in the package's type declarations,
   restricted to names that are runtime exports (types-only deprecations are listed apart);
4. asks the registry for the latest published versions (`--latest`) and reports the drift;
5. compares exports with the catalog (new exports not yet catalogued, catalogued entries no
   longer exported) and with the proven registers (a proven component missing or
   deprecated is a failure, exit code 5);
6. writes `reports/YYYY-MM.md` and stamps `last_verified` into the registers.

Run on the Mac, against the production trees and the latest packages:

    python scripts/verify_components.py --tree <web app> --tree <admin app> --tree <field app> --latest

The workflow `.github/workflows/monthly-components.yml` runs the same script on the first of
the month against freshly installed latest packages and uploads the report; a failure is the
alarm. Register changes are committed from the Mac after the founder reads the report.

Rules: a component enters a register only through the scan; a deprecated proven component
becomes pattern work (the generator moves to the replacement) before the package is upgraded;
nothing here touches the engine.
