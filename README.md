# 🚀 Startup Marketplace Intelligence Analytics

## 🧠 Overview
This project analyzes startup marketplace data from TrustMRR to identify high-performing startups, uncover revenue trends, and highlight investment opportunities using a data-driven approach.

---

## 🎯 Objectives
- Identify top-performing startups
- Analyze revenue patterns across categories
- Evaluate business model effectiveness
- Build a Top 50 investment strategy

---

## 🗂️ Data Source
**Primary Source:**
- TrustMRR API  
  - `/api/v1/startups`
  - `/api/v1/startups/{slug}`

**Data Includes:**
- Revenue (Last 30 days, MRR, Total)
- Growth metrics
- Category & business model
- Customer & subscription data
- Traffic & ranking signals

---

## ⚙️ Data Pipeline

### 🔹 Data Extraction
- Pulled paginated data from API
- Combined list + detailed endpoints

### 🔹 Data Cleaning
- Null category → "Unknown"
- Standardized country codes
- Removed invalid dates (1900 issue)
- Handled missing revenue values
- Converted cents → USD

### 🔹 Feature Engineering
- `primary_revenue` (fallback logic)
- `revenue_status` (Valid / Suspicious)
- `growth_category`
- `business_model`
- `subscription_bucket`
- `score` (ranking metric)

### 🔹 SQL Layer
- Stored cleaned data in SQLite
- Enabled structured queries for analysis

---

## 📊 Power BI Dashboard

### 📄 Page 1: Top 50 Strategy
- KPI Cards: Total Startups, Avg Revenue
- Category-wise revenue
- Category-wise startup count
- Ranked startup table

👉 **Goal:** Identify top-performing products

---

### 📄 Page 2: Opportunity Analysis
- Scatter Plot (Valuation vs Revenue vs Growth)
- Business model distribution
- High-growth startups

👉 **Goal:** Identify investment opportunities

---

### 📄 Page 3: Market Insights
- Revenue tier segmentation
- Category-wise total revenue
- Revenue validity distribution
- Subscription maturity

👉 **Goal:** Understand market structure

---

## 🎨 Design
- Theme: Purple Merit UI
- Accent Color: `#5B21B6`
- Clean, card-based layout

---

## 🧠 Key Insights
- E-commerce & Marketplace dominate revenue
- Subscription models scale better
- Many startups lack verified revenue
- AI & SaaS show strong growth potential
- Several startups have low or zero active users

---

## ⚠️ Limitations
- Some revenue data may be outdated
- Missing fields for certain startups
- Acquire.com not included (JS-heavy scraping)

---

## 🚀 Future Improvements
- Real-time data pipeline
- Selenium-based scraping for dynamic sites
- ML-based scoring model
- Automated refresh system

---

## 🏁 Conclusion
This project demonstrates:
- End-to-end data pipeline development
- Data cleaning & feature engineering
- SQL + Power BI integration
- Business-driven insights for decision making
