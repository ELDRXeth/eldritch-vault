import streamlit as st
import pandas as pd
from supabase import create_client
from collections import defaultdict

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="Eldritch Org Vault", layout="wide")

VERSION = "v0.4.1"
ACCESS_CODE = "Drake4Ever"

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

.access-card {
    border: 1px solid rgba(255,59,59,0.25);
    border-radius: 14px;
    padding: 28px 30px 20px 30px;
    background-color: rgba(0,0,0,0.35);
    box-shadow: 0 0 18px rgba(255,59,59,0.08);
    text-align: center;
    margin-top: 90px;
    margin-bottom: 14px;
}

.access-title {
    color: #FF3B3B;
    font-size: 24px;
    font-weight: 700;
    letter-spacing: 1px;
    margin-top: 10px;
}

.access-subtitle {
    color: #AAAAAA;
    font-size: 13px;
    margin-top: 4px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# ACCESS CONTROL
# =========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:

    left, center, right = st.columns([1.4, 1, 1.4])

    with center:
        st.markdown(
            """
            <div class="access-card">
                <img src="https://robertsspaceindustries.com/media/n9oocsm1fb55zr/logo/3LDR1TCH-Logo.png"
                     width="120"
                     style="display:block; margin:auto;" />
                <div class="access-title">ELDRITCH ORG VAULT</div>
                <div class="access-subtitle">Access authorization required</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        entered_code = st.text_input(
            "Access Code",
            type="password",
            label_visibility="collapsed",
            key="vault_access_code_input"
        )

        if st.button("Enter Vault", key="enter_vault_button", use_container_width=True):
            if entered_code == ACCESS_CODE:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid access code")

    st.stop()

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

user_list = sorted([u["name"] for u in users], key=str.lower)
item_list = sorted([i["name"] for i in items], key=str.lower)

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

def get_total_vault_items(inventory_dict):
    return sum(max(0, qty) for qty in inventory_dict.values())

total_items_stored = get_total_vault_items(inventory)

# =========================================================
# SIDEBAR VERSION
# =========================================================
st.sidebar.markdown(
    f"""
    <div style="
        font-size: 12px;
        color: #9A9A9A;
        margin-bottom: 6px;
        padding-left: 2px;
    ">
        {VERSION}
    </div>
    """,
    unsafe_allow_html=True
)

# =========================================================
# SIDEBAR OVERVIEW
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
        new_user = st.text_input("Add User", key="add_user_input")

        if st.button("Add User", key="add_user_button"):
            if new_user.strip():
                supabase.table("members").insert({"name": new_user.strip()}).execute()
                st.success("User added")
                st.rerun()

    with col2:
        new_item = st.text_input("Add Item", key="add_item_input")

        if st.button("Add Item", key="add_item_button"):
            if new_item.strip():
                supabase.table("items").insert({"name": new_item.strip().lower()}).execute()
                st.success("Item added")
                st.rerun()

    st.divider()

    if not user_list:
        st.warning("Add at least one user before recording transactions.")
    elif not item_list:
        st.warning("Add at least one item before recording transactions.")
    else:
        item = st.selectbox("Item", item_list, key="transaction_item")
        qty = st.number_input("Quantity", min_value=1, step=1, key="transaction_qty")
        action = st.selectbox("Action", ["Deposit", "Withdraw", "Transfer"], key="transaction_action")
        from_user = st.selectbox("From", user_list, key="transaction_from")
        to_user = from_user

        if action == "Transfer":

            transfer_mode = st.radio(
                "Transfer Destination",
                ["Existing User", "New User"],
                horizontal=True,
                key="transfer_mode"
            )

            if transfer_mode == "Existing User":
                to_user = st.selectbox(
                    "Transfer To",
                    user_list,
                    key="transfer_existing_user"
                )
            else:
                to_user = st.text_input(
                    "New User Name",
                    key="transfer_new_user"
                )

        if st.button("Submit Transaction", key="submit_transaction_button"):

            if action == "Transfer" and not to_user.strip():
                st.error("Transfer target cannot be empty.")
            else:
                if action == "Transfer":
                    existing_users = {
                        u["name"].strip().lower()
                        for u in users
                    }

                    if to_user.strip().lower() not in existing_users:
                        supabase.table("members").insert({
                            "name": to_user.strip()
                        }).execute()

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

    if not inventory:
        st.info("No data available.")
    else:
        item_totals = defaultdict(list)

        for (item, user), qty in inventory.items():
            if qty > 0:
                item_totals[item].append((user, qty))

        visible_items = {
            item: owners
            for item, owners in item_totals.items()
            if sum(qty for _, qty in owners) > 0
        }

        if not visible_items:
            st.info("No items currently stored.")
        else:
            for item in sorted(visible_items.keys(), key=str.lower):
                owners = sorted(
                    visible_items[item],
                    key=lambda x: x[0].lower()
                )

                total_item = sum(qty for _, qty in owners)

                with st.expander(f"{item} ({total_item})"):
                    for user, qty in owners:
                        st.write(f"{user}: {qty}")

# =========================================================
# USERS
# =========================================================
elif page == "Users":

    st.title("Users")

    if not user_list:
        st.info("No users found.")
    else:
        for user in user_list:

            holdings = defaultdict(int)

            for (item, owner), qty in inventory.items():
                if owner == user and qty > 0:
                    holdings[item] += qty

            with st.expander(user):
                positive_holdings = {
                    item: qty
                    for item, qty in holdings.items()
                    if qty > 0
                }

                if positive_holdings:
                    for item in sorted(positive_holdings.keys(), key=str.lower):
                        st.write(f"{item}: {positive_holdings[item]}")
                else:
                    st.info("Empty")

# =========================================================
# DATA LOG
# =========================================================
elif page == "Data Log":

    st.title("Data Log")

    if not df.empty:
        display_df = df.copy()

        for column in [
            "id",
            "idx",
            "user_name",
            "notes",
            "location"
        ]:
            if column in display_df.columns:
                display_df = display_df.drop(columns=[column])

        st.dataframe(
            display_df,
            use_container_width=True
        )

    else:
        st.info("No records found.")
