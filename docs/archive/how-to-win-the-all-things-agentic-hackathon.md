# How to Win the All Things Agentic Hackathon: Judging Criteria & Live Q&A Practical Guide

> **Source Video:** [How to Win the All Things Agentic Hackathon: Judging Criteria Live Q&A | Devpost Build Session](https://www.youtube.com/watch?v=DCXjvKmUIGY)  
> **Views:** 1,558 | **Date:** August 26, 2026  
> **Speakers:** Google Cloud's Christina Lin (DevRel Engineering Manager) and Willie Turney (Product Marketing Manager)  
> **Total Prize Pool:** ,000 (,000 Grand Prize) | **Submission Deadline:** August 31, 2026

---

### Core Agenda & Timestamps
- `00:00` Welcome & introductions (Devpost, Google Cloud)
- `02:00` Prize breakdown — K total, K grand prize
- `03:14` The three tracks explained: Taskmaster, Collaborative Partner, Fortified Enterprise Fleet
- `05:41` Judging criteria breakdown: README, architecture diagram, demo video
- `10:06` Live project review: Shipwright — demoing a long-running async agent in 4 minutes
- `11:16` Live project review: Forever Brain — structuring a demo without overwhelming judges
- `12:20` Live Q&A: Which track does my project actually fit?
- `22:07` What "complete" looks like for an architecture diagram
- `22:44` How long judges actually spend per submission
- `28:44` Fortified Enterprise Fleet track: Proving security and governance
- `35:36` What makes memory "agentic" vs. just a chatbot with recall
- `39:19` What to include in your README
- `42:56` Final advice before the deadline

---

To win the **All Things Agentic Hackathon**, judges revealed concrete evaluation priorities and winning strategies during the Live Q&A session. Key takeaways are organized into: packaging the three required deliverables, core judging rubrics, track-specific winning strategies, and tailored project guidance.

---

## I. Winning Packaging for the Three Submission Deliverables

### 1. Demonstration Video: The Critical First Impression

* **The Golden 30-Second Rule:** The video is the very first asset judges review. Deliver a compelling "Wow" hook within the first 30 seconds to immediately grab their attention.
* **Strict 4-Minute Limit:** Judges use strict timers and will stop watching at the 4-minute mark. Keep the presentation concise and tight.
* **Video Content Structure:** Clearly frame the problem pain point followed by your solution. For asynchronous, long-running agent workflows (e.g., app reviews or batch evaluation), introduce the problem, immediately show the end-to-end outcome, and briefly scroll through execution logs to demonstrate real background activity (judges will verify in code).
* **Do NOT Use AI Voiceovers:** Judges strongly encourage authentic personal narration. AI voices lack authentic energy, whereas judges value and reward genuine passion and engineering enthusiasm.
* **Suitable for Broad Social Sharing:** Winning projects are highlighted on Google Cloud social channels; ensure the presentation style is accessible and clear to a broader technical audience.

### 2. README Documentation: The Bridge to Technical Depth

* Judges turn to the README after the video sparks their interest. A well-structured, detailed README is essential for high scores.
* **Must Include:** A concise project overview, a clear directory structure diagram (enabling judges to navigate code quickly), key engineering insights and lessons learned, and deep technical highlights you could not fit into the 4-minute video.

### 3. Architecture Diagram: Clean, Readable, and Consumable

* Evaluated under the architecture rubric. Keep diagrams clean and **consumable** at a glance: where the agent is deployed, which components are involved, and how data and controls flow between them.
* Avoid dense "mini-essay" text blocks in diagrams. AI-generated diagrams (e.g., Mermaid) are fully accepted as long as they accurately represent the physical and logical architecture.

---

## II. Core Judging Rubric

* **Innovation (40% Weight):** The single most impactful category. Judges have reviewed hundreds of submissions and actively reject basic chatbots. Projects must move beyond conversational Q&A to showcase unique, agentic capabilities.
* **Operational Utility:** The project must genuinely execute. Judges possess automated test tooling and will inspect code repositories to verify that claimed functionalities actually work.
* **Architecture Design:** Design must address real operational realities (e.g., for long-running workflows: failure recovery steps, token retry logic, state persistence, error boundaries).
* **Google Cloud Integration (Mandatory Criterion):** Hard requirement to use Gemini models, Google Agent Development Kit (ADK), or Google Cloud services (Cloud Run, Cloud SQL, Firestore, Pub/Sub, etc.).

---

## III. Track-Specific Winning Strategies

* **Taskmaster Track:**
  * Focuses on agents that autonomously execute and complete tasks for humans. Prioritize **depth and intelligence of execution** over artificial multi-day runtimes.
  * **Strategy:** Highlight a single, formidable end-to-end workflow that creates a "Wow" effect rather than multiple trivial happy paths. Document secondary use cases in the README.
* **Collaborative Partner Track:**
  * Focuses on intelligent data ingestion and bidirectional collaboration. Simple vector retrieval is seen as "just a chatbot with recall."
  * **Strategy:** Demonstrate proactive agent behavior, such as self-improving memory loops, proactive user interaction optimization, or triggering external downstream actions.
* **Fortified Enterprise Fleet Track:**
  * Focuses on multi-agent collaboration (swarms). Key criteria include security, auditable execution trails, and robust governance.
  * **Strategy:** Judges favor native integration with Google Cloud Agent Platform features like the Agent Registry.

💡 **Judges' Final Takeaway:** Do not get trapped in perfectionism. **"Submit first"** before the deadline — you never know your chances until you submit. Most importantly, have fun!

---

## Practical Action Items for This Project

### 1. How to Draw a Consumable Architecture Diagram
* **Keep it simple and consumable:** Ensure judges immediately see where the agent runs (Cloud Run), how requests arrive, and how policies evaluate.
* **Avoid text-heavy blocks:** Rely on clear flowchart nodes rather than paragraphs.
* **Mermaid Implementation:** Use a clean 5-step flow (Queue Ingestion → Pre-check Planning → Deterministic Evidence Gathering → Risk Routing R0~R4 → Approval Packet / ControlEvidence Emission).

### 2. Winning Formula for the Taskmaster Track
* **Showcase ONE Formidable Workflow:** Focus demo time on the R4 Hard Block scenario where human override is explicitly rejected by deterministic policy.
* **Demonstrate Execution Depth:** Highlight how 100 queue items are processed in seconds with full deterministic evidence collection, saving 82% of human review time.
* **Actionable Routing:** Show how the agent takes concrete routing actions (Auto-release, Sample, Escalate, Block) and delivers structured Approval Packets exclusively to items requiring human judgment.

### 3. How to Structure README Insights
* Document real architectural revelations encountered during development (e.g., ADK plugin vs. agent-layer short-circuit differences, execution trajectory attribution as an evaluation contract, fail-closed policy enforcement).
