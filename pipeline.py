import requests
import pandas as pd
import time
import json
import sqlite3

# =========================
# CONFIG
# =========================

API_KEY = "Bearer tmrr_6c0965c9d44aef634801469ba1595b36"
BASE_LIST = "https://trustmrr.com/api/v1/startups"
BASE_DETAIL = "https://trustmrr.com/api/v1/startups/"
MAX_PAGES = 30


# =========================
# FETCH LIST DATA
# =========================

def fetch_list():

    headers = {
        "Authorization": API_KEY,
        "Accept": "application/json"
    }

    all_data = []
    seen = set()
    page = 1

    while page <= MAX_PAGES:

        url = f"{BASE_LIST}?page={page}"
        res = requests.get(url, headers=headers)

        print(f"Page {page} → {res.status_code}")

        if res.status_code == 429:
            print("⏳ Rate limit hit → sleeping 60s")
            time.sleep(60)
            continue

        if res.status_code != 200:
            print("❌ Error:", res.text)
            break

        data = res.json().get("data", [])

        if not data:
            break

        new_rows = []
        for item in data:
            slug = item.get("slug")
            if slug not in seen:
                seen.add(slug)
                new_rows.append(item)

        if not new_rows:
            break

        all_data.extend(new_rows)

        page += 1
        time.sleep(1.5)

    df = pd.DataFrame(all_data)
    df["source"] = "TrustMRR"

    print(f"\n✅ Total list rows: {len(df)}")
    return df


# =========================
# FETCH DETAIL DATA
# =========================

def fetch_details(slugs):

    headers = {
        "Authorization": API_KEY,
        "Accept": "application/json"
    }

    details = []

    print("\n🚀 Fetching detail data...\n")

    for i, slug in enumerate(slugs):

        url = BASE_DETAIL + slug
        res = requests.get(url, headers=headers)

        if res.status_code == 429:
            print("⏳ Rate limit hit → sleeping 60s")
            time.sleep(60)
            continue

        if res.status_code != 200:
            print(f"❌ Failed: {slug}")
            continue

        data = res.json().get("data", {})
        details.append(data)

        print(f"{i+1}/{len(slugs)} → {slug}")

        time.sleep(3)  # rate limit safe

    df = pd.DataFrame(details)

    print(f"\n✅ Total detail rows: {len(df)}")
    return df


# =========================
# CLEAN + FEATURE ENGINEERING
# =========================

def clean_data(df):

    def parse_revenue(x):
        try:
            if isinstance(x, dict):
                return x
            if isinstance(x, str):
                return json.loads(x.replace("'", '"'))
        except:
            pass
        return {"mrr": 0, "last30Days": 0, "total": 0}

    # 🔥 USE LIST VERSION
    df["rev"] = df["revenue_list"].apply(parse_revenue)

    df["mrr"] = df["rev"].apply(lambda x: float(x.get("mrr", 0)))
    df["last30"] = df["rev"].apply(lambda x: float(x.get("last30Days", 0)))
    df["total"] = df["rev"].apply(lambda x: float(x.get("total", 0)))

    # ---------- VALIDATION ----------
    def validate(r):
        if r["last30"] > r["total"]:
            return "Invalid"
        if r["mrr"] > r["last30"] * 2:
            return "Invalid"
        if r["last30"] > 1_000_000 and r["mrr"] == 0:
            return "Suspicious"
        return "Valid"

    df["revenue_status"] = df.apply(validate, axis=1)
    df = df[df["revenue_status"] != "Invalid"]

    # ---------- BUSINESS MODEL ----------
    df["business_model"] = df.apply(
        lambda r: "Subscription" if r["mrr"] > 0 else
        ("Transactional" if r["last30"] > 0 else "Unknown"),
        axis=1
    )

    # ---------- PRIMARY REVENUE ----------
    df["primary_revenue"] = df.apply(
        lambda r: r["mrr"] if r["mrr"] > 0 else r["last30"],
        axis=1
    )

    # ---------- VALUATION ----------
    df["askingPrice"] = pd.to_numeric(df.get("askingPrice_list"), errors="coerce")

    df["valuation_multiple"] = df.apply(
        lambda r: r["askingPrice"] / r["primary_revenue"]
        if pd.notna(r["askingPrice"]) and r["primary_revenue"] > 0 else None,
        axis=1
    )

    def valuation(x):
        if pd.isna(x):
            return "Unknown"
        elif x < 3:
            return "Undervalued"
        elif x < 6:
            return "Fair"
        else:
            return "Overvalued"

    df["valuation_status"] = df["valuation_multiple"].apply(valuation)

    return df.drop(columns=["rev"], errors="ignore")


# =========================
# INSIGHTS
# =========================

def generate_insights(df):

    insights = {}

    insights["Top Categories"] = (
        df.groupby("category_list")["primary_revenue"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
    )

    insights["Business Model Split"] = df["business_model"].value_counts()

    insights["Top Startups"] = (
        df.sort_values("primary_revenue", ascending=False)
        [["name_list", "category_list", "primary_revenue"]]
        .head(20)
    )

    insights["Revenue Validity"] = df["revenue_status"].value_counts()

    return insights


# =========================
# SAVE SQL
# =========================

def save_sql(df):
    print("Rows before SQL save:", len(df)) # type: ignore

    df_sql = df.copy()

    for col in df_sql.columns:
        if df_sql[col].dtype == "object":
            df_sql[col] = df_sql[col].astype(str)

    conn = sqlite3.connect("market_intelligence.db")

    df_sql.to_sql("startups_full", conn, if_exists="replace", index=False)
    print("Saving rows:", len(df_sql))

    conn.close()

    print("✅ SQL saved")


# =========================
# SAVE EXCEL
# =========================

def save_excel(raw, clean, insights):

    filename = f"market_intelligence_{int(time.time())}.xlsx"

    with pd.ExcelWriter(filename) as writer:

        raw.to_excel(writer, sheet_name="Raw Data", index=False)
        clean.to_excel(writer, sheet_name="Clean Data", index=False)

        for name, data in insights.items():
            pd.DataFrame(data).to_excel(writer, sheet_name=name)

    print(f"✅ Excel saved: {filename}")


# =========================
# MAIN
# =========================

def run():

    print("\n🚀 Running FULL Pipeline...\n")

    # STEP 1: LIST
    df_list = fetch_list()

    if df_list.empty:
        print("❌ No data fetched")
        return

    # STEP 2: DETAILS
    slugs = df_list["slug"].dropna().tolist()

    # 🔥 testing mode
    # slugs = slugs[:50]

    df_detail = fetch_details(slugs)

    # STEP 3: MERGE
    print("\n🔗 Merging datasets...\n")

    df_full = df_list.merge(
        df_detail,
        on="slug",
        how="left",
        suffixes=("_list", "_detail")
    )

    # STEP 4: CLEAN
    df_clean = clean_data(df_full)

    # STEP 5: INSIGHTS
    insights = generate_insights(df_clean)

    # STEP 6: SAVE
    save_sql(df_clean)
    save_excel(df_list, df_clean, insights)

    print("\n🎯 PIPELINE COMPLETE (FULL DATA ENGINE)")


if __name__ == "__main__":
    run()