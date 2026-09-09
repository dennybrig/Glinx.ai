# Validation record

Validation performed during initial implementation on September 9, 2026:

- Python agent suite: **17 passing tests** covering evidence merging; no implicit collectors; explicit target validation; safe Graph continuation URLs; pagination and managed-identity filtering; token exclusion from reports; client authentication; disabled redirects; partial source failure isolation; CSV connection references; endpoint normalization; DNS inference and lookalikes; failure exit codes and private Unix output permissions.
- JavaScript model suite: **7 passing tests** covering fixture and count consistency; invalid imports; dangling links; duplicate IDs; evidence requirements; rule findings; combined filters; CSV formula escaping; failed/empty scans.
- Real Linux endpoint run: 693 installed package entries examined in the development environment; one endpoint system returned; zero network sources enabled. This minimal environment is not a representative company inventory.
- JavaScript syntax checks and local report contract checks.
- Wheel built offline, installed into a fresh virtual environment, and invoked from outside the repository. Bundled demo generation and the local HTTP server's asset/report routes passed. Traversal and invalid Host requests were rejected. No browser was used for these HTTP checks.

The hosted fixture uses fictional sample data. Microsoft API and DNS behaviors are exercised with synthetic test responses; no live company credentials were available. Windows/macOS collector behavior is implemented but was not executed on real Windows/macOS machines in this session. CI defines those OS jobs; their remote completion is a separate check.

Visual browser testing was not performed in this session. The layout is responsive and uses semantic HTML, keyboard-operable map nodes, native dialogs, escaped imports, and reduced-motion support, but needs a final rehearsal on the presentation browser. This is a prototype rather than a production security certification.
