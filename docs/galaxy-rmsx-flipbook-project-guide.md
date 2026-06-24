# Galaxy/RMSX/Flipbook Project Guide

This document is the working guide for learning how Galaxy tools operate and for using RMSX/Flipbook as the final case study. It preserves the original project brief, then turns it into a structured outline for the orientation report, corpus-building work, repository inspection, and staged integration plan.

## Canonical Project Brief

I want you to help me understand how the Galaxy Project ecosystem works, how Galaxy tools are built, how data moves between tools, how users interact with tools through the web interface, and how one would document and implement a new scientific analysis tool in that ecosystem. The specific final case study will be integrating RMSX and Flipbook into Galaxy as naturally as possible.

RMSX/Flipbook repository:
https://github.com/AntunesLab/rmsx

Galaxy main instance:
https://galaxy-main.usegalaxy.org/

I want this project to produce two things. First, I want a clear, organized, developer-facing guide to how Galaxy tools operate: tool wrappers, XML tool definitions, datatypes, workflows, histories, datasets, collections, dependencies, containers, Planemo testing, Tool Shed conventions, visualizations, and interactive tools. Second, I want to use that understanding to determine the best way to make RMSX and Flipbook work inside Galaxy, ideally allowing users to upload molecular dynamics structures and trajectories, run RMSX, generate plots, and, if feasible, view or export Flipbook-style structural/motion visualizations.

For terminology, Galaxy also has concepts such as workflows, histories, datatypes, dataset collections, visualizations, Galaxy Charts, Tool Shed repositories, and Galaxy Interactive Tools. Part of your job is to clarify these terms and explain which ones matter for RMSX/Flipbook.

I anticipate there being multiple core phases to this.

First, a general overview and exploration phase. In this phase, I want you to map the Galaxy ecosystem and explain how it works from a developer’s perspective. What are the core abstractions? What does a Galaxy tool actually consist of? How does a command-line program become a web-accessible Galaxy tool? How are inputs declared, how are outputs captured, and how does Galaxy keep track of provenance? How do Galaxy workflows connect tools? What role do datatypes and dataset collections play? What is Planemo used for? What is the Tool Shed? What does it mean for a tool to be “Galaxy-native”? What kinds of visualizations are possible inside Galaxy, and what are the limits?

In this first phase, I also want you to identify the best resources to add to our working corpus. This should include current Galaxy developer documentation, Galaxy Training Network materials, Planemo documentation, Tool Shed or IUC guidance, example tool wrappers, and any relevant Galaxy tools that handle structural biology, molecular dynamics, large scientific files, plots, HTML reports, or interactive visualization. Mailing lists and forum posts can be used when helpful, but be cautious about relying on anything that may already be outdated.

After this overview phase, we will inspect the relevant software more closely. We will review the Galaxy tool ecosystem and several representative Galaxy tools or tool suites that solve similar problems. These case studies should not just be listed; I want you to explain how they work programmatically. How do they define their inputs? How do they invoke the underlying command-line software? How do they declare outputs? How do they manage dependencies? How do they test expected behavior? How do they expose results to users? What design patterns should we emulate for RMSX/Flipbook, and what should we avoid?

In parallel, we will inspect RMSX and Flipbook themselves. I want a code-level understanding of what the repository currently does, what the true entry points are, what inputs it expects, what assumptions are hard-coded, what outputs it creates, and what parts are notebook-specific versus reusable. We should determine whether RMSX needs a cleaner command-line interface before it can be wrapped in Galaxy. We should also determine whether Flipbook should be treated as part of the same tool, a separate downstream tool, a generated HTML report, a visualization plugin, or a Galaxy Interactive Tool.

Once those pieces are in place, we will create a hierarchical representation of what we are learning. The goal is to understand Galaxy well enough that the document is useful beyond this one project. I want a structured explanation of the moving parts of Galaxy tool development, including the normal path from command-line tool to Galaxy wrapper to tested local tool to workflow component to potentially shareable Tool Shed tool. I also want comparisons of multiple routes for RMSX/Flipbook: a minimal static-output wrapper, a multi-tool RMSX workflow, a self-contained HTML visualization route, and a more ambitious interactive visualization route.

We should stress test our understanding with small examples and smoke tests. Before trying to build the complete RMSX/Flipbook integration, we should make sure the fundamentals work exactly as we think they do. For example, we should be able to create or inspect a minimal Galaxy wrapper, understand how Planemo tests it, understand how files are staged and named, and understand how outputs appear in the Galaxy history. Then we can apply those lessons to RMSX.

The final implementation plan should be staged. The first likely target should be a minimal, robust Galaxy wrapper for RMSX that accepts a structure and trajectory, exposes the essential parameters, and produces Galaxy-friendly outputs such as tables, plots, logs, and perhaps an HTML report. Later stages can consider separating computation from plotting, adding workflow support, improving packaging, and adding Flipbook-style visualization. The most ambitious stage would be an interactive structure or trajectory viewer using an appropriate Galaxy mechanism, but that should only come after we understand what is realistic and maintainable.

The primary goal is not just to “make RMSX run in Galaxy.” The primary goal is to create a clear developer guide and working corpus for understanding how Galaxy tools operate, with RMSX/Flipbook serving as the final case study and proof of understanding. By the end, the document should be useful to a human developer or an LLM trying to modify, extend, or create Galaxy tools, especially tools involving molecular dynamics, structural biology, plotting, and visualization.

For the immediate first step, do not write implementation code yet. Start by producing an orientation report. Explain the Galaxy concepts and terminology we need, identify the most relevant documentation and example tools, outline the likely integration routes for RMSX/Flipbook, and list the key unknowns we need to resolve by inspecting the RMSX repository and existing Galaxy examples.


Write this prompt to a document. It will be our guide as we delve into this.

## Working Outline

### 1. Orientation Report: Galaxy From a Developer Perspective

- Explain the core Galaxy abstractions: tools, histories, datasets, dataset collections, workflows, datatypes, jobs, dependencies, containers, visualizations, Tool Shed repositories, Galaxy Charts, and Galaxy Interactive Tools.
- Describe how a command-line scientific program becomes a Galaxy web tool through an XML wrapper, declared inputs, command templating, output declarations, dependency metadata, tests, and help text.
- Explain how Galaxy stages data, names files, records job provenance, and exposes tool results back into a user's history.
- Clarify what "Galaxy-native" should mean for this project: predictable inputs and outputs, reproducible jobs, declared dependencies, useful metadata, tests, workflow compatibility, and outputs that make sense in the Galaxy UI.

### 2. Working Corpus: Documentation and Examples to Collect

- Current Galaxy tool developer documentation, especially wrapper XML, tool parameter types, command blocks, output discovery, tests, datatypes, and best practices.
- Galaxy Training Network material on tool development, workflows, histories, collections, reproducibility, and admin/deployment topics only where they affect tool design.
- Planemo documentation for local wrapper development, linting, testing, serving tools, profiles, and Tool Shed packaging.
- IUC and Tool Shed guidance for repository layout, dependency management, test data, macros, citations, help text, and maintainability conventions.
- Representative wrappers for structural biology, molecular dynamics, large binary/text scientific files, plotting tools, HTML reports, and interactive or visualization-heavy outputs.

### 3. Case Studies: Existing Galaxy Tools to Inspect

- Identify tools that accept paired or related scientific inputs, such as structure plus trajectory, reference plus reads, or model plus data.
- Inspect how representative wrappers define input formats, parameter validation, conditional options, repeats, collections, and advanced parameters.
- Compare command invocation patterns: direct CLI calls, helper scripts, generated config files, containerized commands, and tools that gather multiple outputs.
- Compare output patterns: tabular data, plots, logs, directories, HTML reports, composite datatypes, dynamic output discovery, and workflow-friendly named outputs.
- Extract design patterns to emulate for RMSX/Flipbook and traps to avoid, especially brittle filename assumptions, notebook-only workflows, opaque HTML-only outputs, or under-tested visualization paths.

### 4. RMSX/Flipbook Repository Inspection

- Identify true entry points for RMSX computation, plotting, Flipbook generation, and any GUI or notebook-only paths.
- Determine accepted input types for structures, trajectories, metadata, selections, frame ranges, model choices, and parameter files.
- Map outputs produced by each entry point: numeric tables, intermediate files, plots, logs, structural files, rendered animations, HTML, notebooks, or application assets.
- Record hard-coded assumptions about paths, filenames, working directories, installed tools, graphical backends, notebooks, or local-only resources.
- Decide whether RMSX needs a cleaner command-line interface before a robust Galaxy wrapper can be written.

### 5. Candidate Integration Routes

- Minimal Flipbook wrapper: accept a structure and trajectory, expose essential parameters, run RMSX non-interactively, and produce Galaxy-friendly tables, plots, logs, and optional static report assets.
- Multi-tool RMSX workflow: separate preprocessing, RMSX computation, plotting, and report generation so users can reuse outputs in workflows and inspect intermediate datasets.
- Self-contained HTML report route: produce an HTML output that bundles plots and static Flipbook-style visualization artifacts where Galaxy can safely display or download them.
- Galaxy visualization or Charts route: expose selected RMSX outputs through Galaxy's visualization mechanisms if the output data maps naturally to those interfaces.
- Galaxy Interactive Tool route: investigate a richer Flipbook-style interactive viewer only after the static and workflow-friendly path is understood and maintainable.

### 6. Smoke Tests Before Full Integration

- Inspect or create a minimal Galaxy wrapper only as a learning exercise once the orientation corpus is assembled.
- Verify how Planemo linting and tests execute a wrapper, stage inputs, compare outputs, and report failures.
- Confirm how output files appear in a Galaxy history, including names, datatypes, metadata, and provenance.
- Test a small RMSX-like command shape before wrapping the full RMSX/Flipbook workflow.

### 7. Key Unknowns to Resolve Next

- Which current Galaxy documentation pages are authoritative for wrapper XML, datatypes, Planemo, visualizations, and Interactive Tools?
- Which existing Galaxy/IUC tools most closely resemble molecular dynamics structure-plus-trajectory analysis?
- Which structure and trajectory formats should be considered first-class for RMSX/Flipbook in Galaxy?
- Does RMSX already provide a stable non-interactive CLI, or does it need one before wrapping?
- Are RMSX plotting and Flipbook visualization separable from computation in the current repository?
- What output mix best balances Galaxy-native workflow use with useful scientific visualization?
- Can Flipbook-style interactive visualization be safely and maintainably expressed as an HTML report, Galaxy visualization, or Galaxy Interactive Tool?

### 8. First Deliverables After This Guide

- A researched Galaxy orientation report with citations and links to current documentation.
- A curated list of example wrappers and tool suites, grouped by pattern and relevance.
- A code-level RMSX/Flipbook repository inspection report.
- A staged implementation plan for a minimal Flipbook Galaxy wrapper and later visualization routes.
