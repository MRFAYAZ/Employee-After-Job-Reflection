# Design Rationale: The Daily Reflection Tree

## The Core Philosophy

When designing this reflection tree, the primary constraint wasn't technical; it was human. At 7:00 PM, after a long workday, cognitive load is at its peak. If an employee feels like they are taking a personality quiz or being evaluated by HR, they will either abandon the flow or give socially acceptable, dishonest answers.

The goal was to build a **deterministic mirror, not a therapist**. The tree needed to capture the messy reality of human behavior (using established psychology) but encode it into a crisp, auditable, and branching structure. Every choice had to feel like a natural thought, not a trap.

---

## 1. Question Design: Making the Invisible Visible

The hardest part of this assignment was translating abstract psychological concepts into behavioral choices. People don't think of themselves as "entitled" or "externally locused." They think, *"I'm doing all the work around here and nobody cares."* I spent most of my time ensuring the options didn't feel leading. 

* **The "Energy Check" Opening:** Before hitting Axis 1, I added `q_energy_check`. Why? Because trying to force reflection on someone running on fumes feels tone-deaf. By letting the user declare their battery level upfront, the system builds immediate rapport.
* **Behavioral, Not Evaluative Options:** In Axis 2 (Orientation), if you ask someone if they are entitled, everyone says no. Instead, I asked: *"When you stepped up to help, what was driving that?"* One option is *"I was hoping management would notice."* This gently captures Campbell's Psychological Entitlement without making the user feel judged. It measures the *expectation of reciprocity* rather than framing them as a bad teammate.
* **Breaking Symmetry:** I deliberately avoided making every question have exactly four perfectly balanced options. Human thought isn't symmetrical. Sometimes there are three logical reactions to a situation, sometimes five. Giving the tree a slightly asymmetrical shape makes it feel more like a conversation and less like a standardized test.

---

## 2. Psychological Grounding & The Sequence

The tree follows the prescribed sequence—**Locus → Orientation → Radius**—because it mirrors how human beings actually process stress and growth. You can't care about the team (Radius) if you feel entirely powerless (Locus). 

### Axis 1: Locus of Control (Rotter / Dweck)
I didn't want to confuse "Internal Locus" with "Toxic Positivity." If an employee had a terrible day, forcing them to say "I controlled it all!" is invalidating. The questions here are designed to look for *agency within the chaos*. Even if they chose "I felt like I was putting out fires all day," the follow-up asks what their *first reaction* was. Finding the next fixable thing signals an internal locus, even in a bad environment.

### Axis 2: Orientation (Campbell / Organ)
I contrasted Campbell’s Psychological Entitlement with Organ’s Organizational Citizenship Behavior (OCB). The branching here hinges on *why* effort is exerted. The reflection nodes are careful not to moralize. If someone is keeping score, the reflection acknowledges that "wanting fairness is normal," but nudges them to consider the energy cost of that mindset.

### Axis 3: Radius of Concern (Maslow / Batson)
Maslow's Self-Transcendence suggests that orienting outward reduces personal suffering. For the final axis, I forced a deep dive based on whether their gaze was inward (survival mode) or outward (checking the team's temperature). If they were locked into their own work, the follow-up question differentiates between "flow state" (healthy self-focus) and "protecting my peace" (defensive self-focus).

---

## 3. The Branching Logic & Trade-Offs

Building a deterministic system requires saying no to certain dynamic possibilities. Here are the main trade-offs I made:

* **Depth vs. Completion Rates:** I could have built a 60-node tree that deeply psychoanalyzes the user. However, a reflection tool is useless if the drop-off rate is 80%. I capped the tree at 28 nodes. It's long enough to gather meaningful state signals, but short enough to be completed in under 90 seconds.
* **Strict Categorization vs. Nuance:** Because the system uses no LLM at runtime, options are rigid. A user might feel their true feeling is "between" Option A and Option B. To mitigate this, I designed the options to be highly distinct from one another, preventing overlap and forcing a clear, decisive signal for the state tracker.
* **"Tie-Breaker" Defaults:** In the decision nodes (e.g., `state.locus.internal >= state.locus.external`), I defaulted ties to the "growth/internal" side. If an employee shows equal parts victim and victor mentality, reflecting their victor side back to them is a more useful psychological nudge to end their day.

---

## 4. Future Improvements

If I had more time and engineering scope to expand this Knowledge Graph, I would build:

1. **Longitudinal State Tracking:** The current tree is stateless between sessions. The real power of a PDGMS is seeing trends. I would want to track if an employee is stuck in an "external locus" loop for three weeks straight, which is a leading indicator of burnout or a broken company process.
2. **Contextual Dynamic Insertion:** If this integrated with a calendar API, the opening could be, *"I see you had 5 hours of meetings today. How are you holding up?"* Using hard data as the entry point to psychological reflection creates immense trust.
3. **The "Abort" Branch:** Right now, the user must finish the flow. In a real-world scenario, if someone answers "I am completely drained" at node 2, there should be a branch that just says, *"Close the laptop. We'll reflect tomorrow."* Sometimes, forcing reflection is the wrong management practice.