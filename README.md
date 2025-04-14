# SHMAS: Smart Hospital Multi-Agent System

## Inspiration

In the fast-paced world of healthcare, even the smallest delays in hospital operations can have life-or-death consequences. With multiple processes happening simultaneously—patient triage, resource allocation, and doctor scheduling—hospital workflows can quickly become overwhelmed. Our solution to this complex problem? SHMAS (Smart Hospital Multi-Agent System). This innovative system leverages the power of AI and multi-agent coordination to streamline hospital operations, reduce wait times, and ultimately enhance patient care. By automating and optimizing key tasks, SHMAS ensures that hospital staff can focus on providing care, rather than managing logistics. When tasked with building a multi-agent system, we saw an opportunity to not only improve operational efficiency but also save lives by making critical decisions faster and with greater accuracy.

## What it does

*SHMAS (Smart Hospital Multi-Agent System)* is an AI-driven system designed to automate and optimize hospital workflows using multiple autonomous agents. Each agent is responsible for handling a specific part of the hospital's operations, from patient triage to resource allocation and conflict resolution. The system ensures that tasks are completed efficiently, minimizing delays in patient care and optimizing hospital resources. Key features include:

- *Mental Health State Detection*: The system evaluates the urgency of patient cases based on real-time medical data, enabling intelligent prioritization.
- *Agent Collaboration*: Five different agents collaborate to handle specific tasks, share data, and make decisions in real-time.
- *Conflict Resolution*: The system automatically resolves resource conflicts when demand exceeds supply, ensuring optimal resource allocation.
- *Real-Time Dashboarding*: Hospital staff receive live updates on workflow progress, patient statuses, and agent activities.
- *Priority Scoring Formula*: A dynamic scoring system prioritizes patients in waiting queues based on vital signs, age, and symptoms, ensuring critical cases are addressed first.

### The Five Agents:
1. *Mental Health Analyzer Agent*: Analyzes patient data to assess mental health conditions, prioritizing cases based on urgency.
2. *Triage Agent*: Helps prioritize patient cases based on severity, ensuring critical patients are directed to the appropriate department.
3. *Bed Manager Agent*: Manages available hospital beds, allocating them based on patient severity and available resources.
4. *Doctor Scheduler Agent*: Automates the scheduling of doctors based on patient needs and doctor availability.
5. *Conflict Resolver*: Resolves resource allocation conflicts when multiple agents require the same resources.

## How we built it

We built SHMAS using a combination of AI techniques and tools that allowed for the seamless interaction and orchestration of multiple agents. The tech stack and approach included:

- *LangGraph*: This was used to structure and orchestrate the workflows of our five agents, ensuring clear transitions and proper coordination.
- *Groq APIs*: We integrated large language models (LLMs) via Groq to process data and support decision-making.
  - The *model_name="deepseek-r1-distill-llama-70b"* from Groq was utilized to enhance the decision-making capabilities of the system.
- *Database Management: We used **PostgreSQL* to store and retrieve hospital data securely, ensuring that multiple agents could work with up-to-date and consistent information.
- *Real-Time Updates*: We built a dynamic dashboard to display live information on patient statuses, agent activities, and workflow progress.
- *Priority Score Formula*: We designed and implemented an algorithm that assigns priority scores to patients based on vital signs, symptom severity, and other factors to ensure the right patients are treated first.

## Challenges we ran into

- *Agent Orchestration*: Managing the interactions between multiple agents with interdependencies posed a challenge. Coordinating these agents in real-time required careful state management.  
  *Solution: We implemented **LangGraph* to ensure smooth coordination and transition between agents, allowing them to collaborate effectively while avoiding conflicts.

- *Conflict Resolution*: High-demand situations led to resource contention, creating edge cases where multiple agents wanted to access the same resources.  
  *Solution: We developed a sophisticated **priority scoring system* that factors in multiple variables like patient vitals, age, and symptom severity to prioritize patients appropriately during peak times.

- *Real-Time Data Handling*: Ensuring real-time data updates while avoiding data inconsistency between multiple agents was a complex issue.  
  *Solution: We utilized **transaction management* and *database triggers* to prevent race conditions and ensure consistent data across agents.

- *LLM Integration*: Integrating LLMs within hospital protocols posed challenges in terms of balancing flexibility and deterministic processes.  
  *Solution: We designed precise prompts and implemented **post-processing validation* to ensure that LLM outputs were accurate and aligned with the needs of hospital operations.

## Accomplishments that we're proud of

- *Mental Health Detection and Prioritization*: We successfully developed a system that evaluates the urgency of patient cases and prioritizes them accordingly.
- *AI Agent Collaboration*: We designed and implemented five autonomous agents that communicate and collaborate effectively to handle various hospital processes.
- *Real-Time Dashboarding*: Our real-time dashboard provides valuable insights into hospital workflows, enhancing operational visibility and decision-making.
- *Innovative Priority Score Formula*: We created an innovative algorithm for prioritizing patients in waiting queues, factoring in various aspects such as vitals, age, and symptom severity.
- *Conflict Resolution System*: We built an automated conflict resolution mechanism that optimizes resource allocation in high-demand scenarios without human intervention.

## What we learned

Throughout this project, we gained insights into several key areas:

- *AI Agents*: How to design and implement multiple AI agents that can operate autonomously while collaborating and resolving conflicts in real-time.
- *Communication Between AI Agents*: We explored how agents can communicate effectively, sharing data and making decisions that align with the hospital’s priorities.
- *LLM Integration: How to call and integrate large language models (LLMs) using APIs like **Groq* for data processing and decision-making.
- *LangGraph*: We learned how LangGraph can help orchestrate and structure agent workflows, ensuring clear state transitions and coordinated agent activities.
- *Hospital Intricacies*: We gained a deep understanding of the challenges hospitals face, such as resource management, patient prioritization, and workflow bottlenecks.

## What's next for SHMAS: Smart Hospital Multi-Agent System

The current implementation demonstrates the core functionality of the multi-agent system, but several enhancements could further improve the system:

- *Machine learning models* to predict patient flow and optimize resource allocation.
- *Integration with electronic health records* for more comprehensive patient history.
- *Real-time notifications and alerts* for critical resource shortages.
- Expanded *dashboard with predictive analytics* for hospital administration.
- *Mobile interface* for staff to monitor and manage patient flow remotely.
