# Ctrl-BIAS: EASL Framework for Measuring Bias in Large Language Models

This repository implements and documents the **Ctrl-BIAS** project — an adaptation of the **EASL (Efficient Annotation of Scalar Labels)** (Sakaguchi & Van Durme, 2018) framework for evaluating bias in Large Language Model (LLM) outputs.  

It provides all components needed to reproduce the workflow, from prompt generation through to statistical analysis.

---

## Purpose

The Ctrl-BIAS pipeline combines **human judgment** with **automated Bayesian updating** to measure bias efficiently across multiple domains:

- **Gender in Occupation**
- **Worldview (Individualism ↔ Collectivism)**
- **Power Distance (Low ↔ High)**
- **Bloc Tilt (West ↔ BRICS)**

By using EASL, each bias stream can be evaluated with fewer redundant ratings while maintaining reliable statistical confidence.

---

## Repository Structure

```text
LLM-Bias-Analysis/
│
├── 1.prompts/                     → Prompt design templates and full prompt sets
│
├── 2.outputs/                     → Raw model responses generated from each prompt
│
├── 3.code/                        → Core EASL engine (initialize, main, easl)
│   └── MTurk/                     → Scripts and HTML templates for MTurk integration
│
├── 4.annotations/                 → Rated outputs, updated models, and stopping criteria docs
│
├── 5.analysis/                    → Data cleaning, merging, validation, and statistical analysis
│   ├── 4.visualisation/           → Plot scripts and data for stacked, Beta-PDF, and heatmap visuals
│   └── 5.statistical_testing/     → Kruskal–Wallis / Mann-Whitney U test automation
│
├── SYSTEM_MAINTENANCE_GUIDE.pdf   → Defines how the Ctrl-BIAS EASL pipeline should be maintained
|
├── USER_GUIDE.pdf                 → Full workflow guide for researchers
│
└── README.md                      → This document
```

### Workflow Summary

- **Prompts** — Design domain-specific questions.  
- **Outputs** — Collect model responses for each prompt.  
- **Code (EASL)** — Use the EASL engine to generate HITs, collect ratings, and update posterior bias scores.  
- **Annotations** — Store all rated results and updated model files.  
- **Analysis** — Clean, visualise, and test statistical differences across models.  

---

### Key Concepts

- **Alpha / Beta parameters:** capture uncertainty in bias ratings using a Beta distribution.  
- **Mode / Variance columns:** summarise evolving bias estimates.  
- **EASL iterations:** dynamically prioritise outputs with highest rating uncertainty.  
- **Stopping criteria:** define when further annotation adds minimal statistical gain.  
