All Things Agentic Hackathon Summary Notes

This global hackathon offers a $180,000 prize pool to build autonomous, multi-step AI agents leveraging Gemini 3.5 and Google Cloud ($150 GCP credits provided upon registration).

Challenge Tracks (Choose One)

* Track 1: The Taskmaster
  
  * Core Focus: Action-oriented automation rather than standard chat interfaces.

  * Scope: Solve complex, multi-step chores across work or personal workflows by taking autonomous action and routing data across external systems.

* Track 2: The Collaborative Partner
  
  * Core Focus: Adaptive guidance and collaborative decision-making.

  * Scope: Guide users step-by-step, ask clarifying questions, and continuously adapt to user feedback and thinking patterns.

* Track 3: The Fortified Enterprise Fleet
  
  * Core Focus: Scalable, secure, and compliant multi-agent networks integrated with production systems.

  * Architecture Components:

    * Discovery & Lifecycle: Agent Registry for publishing, versioning, and discovery.

    * Core Execution & State: Agent Runtime (long-running background execution) and Memory Bank (persistent cross-session context).

    * Security & Governance: Agent Identity (zero-trust access), Agent Gateway (unified routing/policy), and Model Armor (guardrails against prompt injection, tool poisoning, and PII leaks).

    * Telemetry: Agent Observability (OpenTelemetry-compliant audit logs and reasoning traces).

Mandatory Technical Requirements

1. AI Model: Gemini 3.5 or newer accessed via Gemini API or Vertex AI.
  
2. Agent Framework: At least one Google framework (Google ADK, GenAI SDK, Antigravity SDK, or GenKit).
  
3. Cloud Infrastructure: At least one Google Cloud service (e.g., Cloud Run, Cloud SQL, Firestore, GKE, Pub/Sub).
  
Judging Criteria

```
| Criteria                              | Weight | Focus Areas                                                                                             |
| ------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------- |
| Innovation & Operational Utility      | 40%    | Real-world friction removed autonomously; emphasizes functional execution over conversation.            |
| Architectural Discipline & Tech Stack | 30%    | System decoupling, state/memory persistence, credential security, and fault tolerance.                  |
| Demo & Production Readiness           | 30%    | Live demo quality, architecture clarity, reproducible setup guide, and visible proof of GCP deployment. |
```

Submission Checklist

* [ ] Category/Track Selection
  
* [ ] Project Description: Features, tech stack, data sources, and findings/learnings.
  
* [ ] Architecture Diagram: Visual mapping of Gemini, backend services, databases, and frontend interfaces.
  
* [ ] Code Repository (GitHub / GitLab / Bitbucket): Must include a reproducible setup guide (README.md). If private, grant access to <testing@devpost.com> and <cloudhackathons@google.com>.
  
* [ ] ~4-Minute Demo Video: Problem overview, value proposition, live end-to-end demo, and visible proof of running on Google Cloud (e.g., Cloud Run console, Vertex AI logs, .run domain).
  
* [ ] Hosted Project Link (Optional): Public web UI, extension, or mobile build (strongly encouraged).
  
Bonus Points

* Public Content Creation: Publish an article, podcast, or video (Medium, dev.to, YouTube) detailing how the project was built, stating it was made for this hackathon.
  
* Social Promotion: Share on X, LinkedIn, Instagram, or Facebook using #AllThingsAgenticHackathon.
  
* Google AI Model Integration: Integrate additional Google models such as Gemma, Veo, or Lyria.
Prize Distribution

```
| Prize Category                    | Winners | Cash (USD) | GCP Credits (USD) | Additional Perks                               |
| --------------------------------- | ------- | ---------- | ----------------- | ---------------------------------------------- |
| Grand Prize                       | 1       | $50,000    | $5,000            | Virtual Coffee with Google Team + Social Promo |
| Track Winners (3 Tracks)          | 1 each  | $20,000    | $2,000            | Virtual Coffee with Google Team + Social Promo |
| Startup Excellence (Incorporated) | 1       | $20,000    | $5,000            | Virtual Coffee with Google Team + Social Promo |
| Individual / Hobbyist             | 2       | $10,000    | $1,000            | Virtual Coffee with Google Team + Social Promo |
| Best Architectural Design         | 2       | $5,000     | $1,000            | —                                              |
| Best Multimodal UX                | 2       | $5,000     | $1,000            | —                                              |
| Honorable Mentions                | 5       | $2,000     | $500              | —                                              |

```
