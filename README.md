# Training Dashboard / Athlete Analytics Dashboard

A Streamlit web app for analyzing endurance training data, inspired by TrainingPeaks-style dashboards. This project extends my Excel-based workflow into a scalable analytics platform with advanced metrics, GPX parsing, and interactive visualizations.

---

## 📌 Project Goal

The goal is to build a fully modular **Python training analytics system** that eventually becomes a deployable web platform for athletes.  
This system expands on my current Excel pipeline and aims to:

- Parse **GPX files** (Garmin/Strava style)
- Compute reliable **cycling & running TSS, TSB, IF, KJ, Watts/kg**, HR/power zone metrics
- Track **sleep, recovery, carbs, sodium intake**
- Generate **interactive trending graphs** for performance and fatigue
- Mimic TrainingPeaks metrics while remaining fully local and customizable
- Evolve into a **public web dashboard / SaaS tool**

---

## 🚀 Features

- Load **master Excel logs**
- Parse **GPX ride/run files**
- Compute:
  - TSS, IF, NP
  - KJ & calorie burn
  - Watts/kg
  - Running TSS (pace‑based)
- Recovery scoring using **sleep + TSB**
- Plotly visualizations:
  - TSS/CTL/ATL/TSB charts
  - Sleep trends
  - Carbs & sodium intake patterns
  - Power, speed, HR analysis
- Modular structure for advanced expansion

---

## 🛠️ Installation

1. Clone the repo:
```bash
git clone https://github.com/luis33k/PowerSummit.git
cd training-dashboard

© 2025 Luis G. All Rights Reserved.
No part of this repository may be copied, reproduced, distributed, or modified without explicit written permission.
