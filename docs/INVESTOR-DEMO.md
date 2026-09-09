# Glinx · five-minute investor walkthrough

Before presenting, open the hosted private demo as the owner or run `python -m glinx_discovery demo --serve` locally. The local sample demonstration works without a cloud connection or company credentials. Use screen sharing for the private hosted version; it is not an anonymously accessible investor link.

**Frame the vision — 30 seconds.**

“Glinx is building a living self-model of the enterprise. Before a company can diagnose itself or coordinate intelligent action, it needs to know what it runs on and how trustworthy that knowledge is. This is our first sensing layer.”

**Show discovery — 60 seconds.**

Click **Replay discovery**. Say: “This is a fictional manufacturing company. The replay shows the evidence arriving from endpoint inventory, mail DNS, identity registrations, and the owner's inventory.” Point to systems appearing on the map and the 12-system inventory. Do not describe the replay as a live scan.

**Show the evidence — 60 seconds.**

Select **Epicor Kinetic**. Explain the difference between an observed installation record and owner-reported operating context. Then inspect **Microsoft 365**, whose DNS record is a clue requiring verification. “Glinx must know the difference between something it observed, something someone reported, and something it inferred.”

**Show useful questions — 60 seconds.**

Open **Evidence & gaps**. Review the three unassigned systems and the mail-provider clue. Explain that these are transparent inventory rules, not measured savings or an AI operational diagnosis. Inspect the source that remains unconfigured.

**Show the bridge to a real company — 60 seconds.**

Use a real endpoint report that you reviewed beforehand. Import it with **Import scan**. The map now reflects that report and its explicit discovery boundary. If no suitable company report is available, show the install instructions and explain the remaining tenant setup; do not present the sample as real data.

**Close on the next milestone — 30 seconds.**

“The next step is an approved pilot: connect the identity layer and one ERP, give every finding provenance and an owner, and keep the model current. From there, Glinx can reason over native business evidence and recommend actions for people to approve.”

## Questions to be ready for

| Investor question | Accurate answer today |
|---|---|
| Does it discover everything automatically? | It discovers metadata visible to authorized sources. Other devices, SaaS accounts, and isolated networks need additional sources. |
| Is this only a mockup? | The sample replay is a demo. The Python agent, evidence normalization, report pipeline, and viewer are implemented. Live Linux collection has been exercised; real tenant and Windows/macOS pilots remain. |
| Can it read our ERP transactions? | This version identifies ERP presence through fingerprints and inventory. Native transaction/schema connectors are a next increment. |
| Is an LLM running this? | Discovery and current review questions are deterministic. The later reasoning layer will consume the evidence plane. |
| Where is company data stored? | In a local JSON report and browser memory. No report is automatically sent to the hosted demo. |
| How will this scale? | Fleet enrollment, identity reconciliation, durable ingestion, permission-aware connectors, and change history are the next engineering milestones. |
| Can our engineers contribute? | Yes. The private GitHub repository includes a modular collector interface, tests, CI, and contributor instructions. |
