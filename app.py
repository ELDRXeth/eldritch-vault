import streamlit as st
import pandas as pd
from supabase import create_client
from collections import defaultdict

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="Eldritch Org Vault", layout="wide")

# =========================================================
# THEME
# =========================================================
st.markdown("""
<style>

.stApp {
    background-color: #050607;
    color: #E6E6E6;
}

section[data-testid="stSidebar"] {
    background-color: #070A0C;
    border-right: 1px solid rgba(255,59,59,0.18);
}

h1, h2, h3, h4 {
    color: #E6E6E6 !important;
    letter-spacing: 0.5px;
}

div[data-testid="stExpander"] {
    border: 1px solid rgba(255,59,59,0.18);
    border-radius: 10px;
    background-color: rgba(0,0,0,0.25);
}

button {
    border: 1px solid rgba(255,59,59,0.35) !important;
    color: #FF3B3B !important;
    background-color: transparent !important;
}

input, select, textarea {
    background-color: #0A0E10 !important;
    color: #E6E6E6 !important;
    border: 1px solid rgba(255,59,59,0.22) !important;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# SUPABASE
# =========================================================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# =========================================================
# DATA
# =========================================================
def get_users():
    return supabase.table("members").select("*").execute().data or []

def get_items():
    return supabase.table("items").select("*").execute().data or []

def get_transactions():
    return supabase.table("transactions").select("*").order("created_at", desc=True).execute().data or []

users = get_users()
items = get_items()
transactions = get_transactions()

user_list = [u["name"] for u in users]
item_list = [i["name"] for i in items]

df = pd.DataFrame(transactions)

# =========================================================
# INVENTORY ENGINE
# =========================================================
def build_inventory(df):
    inv = defaultdict(int)

    if df.empty:
        return inv

    for _, r in df.iterrows():
        item = r["item_name"]
        qty = int(r["quantity"])
        action = r["action"]

        from_user = r.get("from_owner")
        to_user = r.get("to_owner") or from_user

        if action == "Deposit":
            inv[(item, to_user)] += qty

        elif action == "Withdraw":
            inv[(item, from_user)] -= qty

        elif action == "Transfer":
            inv[(item, from_user)] -= qty
            inv[(item, to_user)] += qty

    return inv

inventory = build_inventory(df)

# =========================================================
# 🔥 FIX: TRUE TOTAL VAULT COUNT
# =========================================================
def get_total_vault_items(inventory_dict):
    return sum(max(0, qty) for qty in inventory_dict.values())

total_items_stored = get_total_vault_items(inventory)

# =========================================================
# SIDEBAR OVERVIEW (FIXED)
# =========================================================
st.sidebar.markdown(
    f"""
    <div style="
        font-size: 12px;
        line-height: 1.5;
        color: #CFCFCF;
        padding: 8px 10px;
        border: 1px solid rgba(255,59,59,0.15);
        border-radius: 8px;
        margin-bottom: 10px;
        background-color: rgba(0,0,0,0.25);
        white-space: nowrap;
    ">
        <strong style="color:#FF3B3B;">Vault Overview</strong><br>
        Users: {len(user_list)} &nbsp;|&nbsp;
        Items Stored: {total_items_stored} &nbsp;|&nbsp;
        Transactions: {len(df)}
    </div>
    """,
    unsafe_allow_html=True
)

# =========================================================
# SIDEBAR BRANDING
# =========================================================
st.sidebar.markdown(
    """
    <div style="
        border: 1px solid rgba(255,59,59,0.25);
        border-radius: 12px;
        padding: 12px;
        text-align: center;
        margin-bottom: 15px;
        background-color: rgba(0,0,0,0.35);
    ">
        <img src="https://robertsspaceindustries.com/media/n9oocsm1fb55zr/logo/3LDR1TCH-Logo.png"
             width="110"
             style="display:block; margin:auto;" />
        <h3 style="margin-top:10px; color:#FF3B3B;">ELDRITCH ORG VAULT</h3>
    </div>
    """,
    unsafe_allow_html=True
)

# =========================================================
# NAVIGATION
# =========================================================
page = st.sidebar.radio(
    "Navigation",
    [
        "Vault Entries",
        "Vault Storage",
        "Users",
        "Data Log"
    ]
)

# =========================================================
# VAULT ENTRIES
# =========================================================
if page == "Vault Entries":

    st.title("Vault Entries")

    col1, col2 = st.columns(2)

    with col1:
        new_user = st.text_input("Add User")

        if st.button("Add User"):
            if new_user.strip():
                supabase.table("members").insert({"name": new_user.strip()}).execute()
                st.success("User added")
                st.rerun()

    with col2:
        new_item = st.text_input("Add Item")

        if st.button("Add Item"):
            if new_item.strip():
                supabase.table("items").insert({"name": new_item.strip().lower()}).execute()
                st.success("Item added")
                st.rerun()

    st.divider()

    item = st.selectbox("Item", item_list)
    qty = st.number_input("Quantity", min_value=1, step=1)
    action = st.selectbox("Action", ["Deposit", "Withdraw", "Transfer"])
    from_user = st.selectbox("From", user_list)
    to_user = from_user

    if action == "Transfer":
        to_user = st.selectbox("Transfer To", user_list)

    if st.button("Submit Transaction"):
        supabase.table("transactions").insert({
            "item_name": item,
            "quantity": qty,
            "action": action,
            "from_owner": from_user,
            "to_owner": to_user
        }).execute()
        st.success("Transaction recorded")
        st.rerun()

# =========================================================
# VAULT STORAGE
# =========================================================
elif page == "Vault Storage":

    st.title("Vault Storage")

    if df.empty:
        st.info("No data available.")
    else:

        grouped = defaultdict(list)

        for _, r in df.iterrows():
            item = r["item_name"]
            qty = int(r["quantity"])
            action = r["action"]

            from_user = r.get("from_owner")
            to_user = r.get("to_owner") or from_user

            if action == "Deposit":
                grouped[(item, to_user)].append(qty)

            elif action == "Withdraw":
                grouped[(item, from_user)].append(-qty)

            elif action == "Transfer":
                grouped[(item, from_user)].append(-qty)
                grouped[(item, to_user)].append(qty)

        item_totals = defaultdict(list)

        for (item, user), qtys in grouped.items():
            total = sum(qtys)
            item_totals[item].append((user, total))

        for item, owners in item_totals.items():
            total_item = sum(q for _, q in owners)

            with st.expander(f"{item} ({total_item})"):
                for user, qty in owners:
                    st.write(f"{user}: {qty}")

# =========================================================
# USERS
# =========================================================
elif page == "Users":

    st.title("Users")

    if df.empty:
        st.info("No data available.")
    else:

        for user in user_list:

            holdings = defaultdict(int)

            for _, r in df.iterrows():
                item = r["item_name"]
                qty = int(r["quantity"])
                action = r["action"]

                from_user = r.get("from_owner")
                to_user = r.get("to_owner") or from_user

                if action == "Deposit" and to_user == user:
                    holdings[item] += qty

                elif action == "Withdraw" and from_user == user:
                    holdings[item] -= qty

                elif action == "Transfer":
                    if from_user == user:
                        holdings[item] -= qty
                    if to_user == user:
                        holdings[item] += qty

            with st.expander(user):
                if holdings:
                    for item, qty in holdings.items():
                        st.write(f"{item}: {qty}")
                else:
                    st.info("Empty")

# =========================================================
# DATA LOG
# =========================================================
elif page == "Data Log":

    st.title("Data Log")

    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No records found.")