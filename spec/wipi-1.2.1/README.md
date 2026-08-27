# WIPI 1.2.1 API catalog

`api.csv` is the canonical source for the current bootstrap declarations and
Samsung/KTF veneers. It contains public API facts, not implementation copied
from the evidence repository, and its 239 rows are not presented as every
WIPI-C generation's complete surface.

Columns:

- `ordinal`, `family`, `name`, `prototype`: standard-facing API inventory;
- `implementation`: local runtime or profile table;
- `abi_class`: veneer generation policy;
- `ktf_samsung_*`: profile-scoped selector evidence;
- `evidence`: privacy-safe source locator.

The ten candidate selectors are all C standard-library entries. `libwipi`
implements that surface locally and does not call those unconfirmed slots.
The importer accepts only the reviewed `confirmed_firmware_selector` and
`candidate_selector` source states. Any new or misspelled evidence state is an
error rather than an implicit candidate conversion.

LGT numbered-import method IDs do not come from API order and do not belong in
the KTF selector columns. Their profile candidates are in
`spec/profiles/lgt-raptor.json`; the narrower methods confirmed for the pinned
ARAM/WIE runtime are in `spec/install/aram-wie-raptor.json` and generate their
own veneer file.
