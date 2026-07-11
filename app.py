import streamlit as st
import pandas as pd
from supabase import create_client
from collections import defaultdict

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="Eldritch Org Vault", layout="wide")

VERSION = "v0.6.0-dev3"
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
# ONE-TIME CONFIRMATION NOTIFICATIONS
# =========================================================
def queue_confirmation(message):
    st.session_state["confirmation_message"] = message


if "confirmation_message" in st.session_state:
    st.toast(st.session_state.pop("confirmation_message"))

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


def get_currency_log():
    return supabase.table("currency_log").select("*").order("created_at", desc=True).execute().data or []


users = get_users()
items = get_items()
transactions = get_transactions()
currency_log = get_currency_log()

user_list = sorted([u["name"] for u in users], key=str.lower)
item_list = sorted([i["name"] for i in items], key=str.lower)

item_df = pd.DataFrame(transactions)
currency_df = pd.DataFrame(currency_log)

# Preserve the existing variable name used by the inventory engine.
df = item_df

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
    # Use the true net quantity so negative balances remain visible
    # instead of being silently ignored.
    return sum(inventory_dict.values())


def get_auec_balance(currency_rows):
    balance = 0

    for row in currency_rows:
        amount = int(row.get("amount") or 0)
        action = row.get("action")

        if action == "Deposit":
            balance += amount
        elif action == "Withdraw":
            balance -= amount

    return balance


total_items_stored = get_total_vault_items(inventory)
auec_balance = get_auec_balance(currency_log)

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
        "AUEC Vault",
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
                queue_confirmation(f"User added: {new_user.strip()}")
                st.rerun()

    with col2:
        new_item = st.text_input("Add Item", key="add_item_input")

        if st.button("Add Item", key="add_item_button"):
            if new_item.strip():
                supabase.table("items").insert({"name": new_item.strip().lower()}).execute()
                queue_confirmation(f"Item added: {new_item.strip().lower()}")
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

        item_description = st.text_area(
            "Reason / Description (optional)",
            key="item_transaction_description"
        )

        available_quantity = inventory.get((item, from_user), 0)
        removes_inventory = action in ["Withdraw", "Transfer"]
        exceeds_inventory = removes_inventory and qty > available_quantity
        allow_item_overdraw = False

        if exceeds_inventory:
            shortage = qty - available_quantity
            st.warning(
                f"{from_user} currently holds {available_quantity} {item}, "
                f"but this {action.lower()} requests {qty}. "
                f"The resulting balance would be {-shortage}."
            )
            allow_item_overdraw = st.checkbox(
                "Allow this transaction and create a negative inventory balance",
                key="allow_item_overdraw"
            )

        if st.button("Submit Transaction", key="submit_transaction_button"):

            if action == "Transfer" and not to_user.strip():
                st.error("Transfer target cannot be empty.")
            elif exceeds_inventory and not allow_item_overdraw:
                st.error(
                    "This transaction exceeds the available inventory. "
                    "Enable the override checkbox to proceed."
                )
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

                cleaned_item_description = item_description.strip() or None

                supabase.table("transactions").insert({
                    "item_name": item,
                    "quantity": qty,
                    "action": action,
                    "from_owner": from_user,
                    "to_owner": to_user,
                    "notes": cleaned_item_description
                }).execute()

                if action == "Deposit":
                    confirmation = f"Deposited {qty} {item} for {from_user}"
                elif action == "Withdraw":
                    confirmation = f"Withdrew {qty} {item} from {from_user}"
                else:
                    confirmation = (
                        f"Transferred {qty} {item} from {from_user} to {to_user.strip()}"
                    )

                queue_confirmation(confirmation)
                st.rerun()

# =========================================================
# VAULT STORAGE
# =========================================================
elif page == "Vault Storage":

    title_col, filter_col = st.columns([0.72, 0.28])

    with title_col:
        st.title("Vault Storage")

    with filter_col:
        show_nonpositive_items = st.checkbox(
            "Show zero / negative balances",
            value=False,
            key="show_nonpositive_vault_items"
        )

    if not inventory:
        st.info("No data available.")
    else:
        item_totals = defaultdict(list)

        # Preserve every owner balance so audit mode can reveal zero and
        # negative positions without changing the underlying ledger math.
        for (item, user), qty in inventory.items():
            item_totals[item].append((user, qty))

        visible_items = {}

        for item, owners in item_totals.items():
            net_total = sum(qty for _, qty in owners)

            # Keep the normal vault view clean. Audit mode reveals items whose
            # organization-wide balance is zero or negative.
            if net_total > 0 or show_nonpositive_items:
                visible_items[item] = owners

        if not visible_items:
            if show_nonpositive_items:
                st.info("No item balances found.")
            else:
                st.info("No positively stocked items currently stored.")
        else:
            for item in sorted(visible_items.keys(), key=str.lower):
                owners = sorted(
                    visible_items[item],
                    key=lambda x: x[0].lower()
                )

                net_total = sum(qty for _, qty in owners)

                with st.expander(f"{item} ({net_total})"):
                    displayed_owner = False

                    for user, qty in owners:
                        # In the normal view, zero owner rows add clutter. In
                        # audit mode, show them alongside negative balances.
                        if qty != 0 or show_nonpositive_items:
                            st.write(f"{user}: {qty}")
                            displayed_owner = True

                    if not displayed_owner:
                        st.info("All recorded user balances are zero.")

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
                if owner == user and qty != 0:
                    holdings[item] += qty

            with st.expander(user):
                nonzero_holdings = {
                    item: qty
                    for item, qty in holdings.items()
                    if qty != 0
                }

                if nonzero_holdings:
                    for item in sorted(nonzero_holdings.keys(), key=str.lower):
                        st.write(f"{item}: {nonzero_holdings[item]}")
                else:
                    st.info("Empty")

# =========================================================
# AUEC VAULT
# =========================================================
elif page == "AUEC Vault":

    st.title("AUEC Vault")

    st.metric("Current Balance", f"{auec_balance:,.0f} aUEC")

    st.divider()

    currency_action = st.selectbox(
        "Action",
        ["Deposit", "Withdraw"],
        key="currency_action"
    )

    currency_amount = st.number_input(
        "Amount",
        min_value=1,
        step=1,
        key="currency_amount"
    )

    currency_description = st.text_area(
        "Reason / Description (optional)",
        key="currency_description"
    )

    exceeds_auec_balance = (
        currency_action == "Withdraw"
        and currency_amount > auec_balance
    )
    allow_auec_overdraw = False

    if exceeds_auec_balance:
        shortage = int(currency_amount) - auec_balance
        st.warning(
            f"This withdrawal exceeds the current AUEC balance by "
            f"{shortage:,.0f} aUEC. The resulting balance would be "
            f"{auec_balance - int(currency_amount):,.0f} aUEC."
        )
        allow_auec_overdraw = st.checkbox(
            "Allow this withdrawal and create a negative AUEC balance",
            key="allow_auec_overdraw"
        )

    if st.button("Submit AUEC Entry", key="submit_currency_entry"):
        if exceeds_auec_balance and not allow_auec_overdraw:
            st.error(
                "This withdrawal exceeds the current balance. "
                "Enable the override checkbox to proceed."
            )
        else:
            cleaned_currency_description = currency_description.strip() or None

            supabase.table("currency_log").insert({
                "action": currency_action,
                "amount": int(currency_amount),
                "description": cleaned_currency_description
            }).execute()

            queue_confirmation(
                f"{currency_action} recorded: {int(currency_amount):,} aUEC"
            )
            st.rerun()

    st.divider()
    st.subheader("Recent Activity")

    if currency_df.empty:
        st.info("No AUEC entries found.")
    else:
        recent_currency_df = currency_df.copy().head(10)

        if "amount" in recent_currency_df.columns:
            recent_currency_df["amount"] = recent_currency_df["amount"].apply(
                lambda amount: f"{int(amount):,}"
            )

        for column in ["id", "idx"]:
            if column in recent_currency_df.columns:
                recent_currency_df = recent_currency_df.drop(columns=[column])

        st.dataframe(
            recent_currency_df,
            use_container_width=True
        )

# =========================================================
# DATA LOG
# =========================================================
elif page == "Data Log":

    st.title("Data Log")

    item_log_tab, auec_log_tab = st.tabs(["Items", "AUEC"])

    with item_log_tab:
        if not item_df.empty:
            display_item_df = item_df.copy()

            for column in [
                "id",
                "idx",
                "user_name",
                "location"
            ]:
                if column in display_item_df.columns:
                    display_item_df = display_item_df.drop(columns=[column])

            if "notes" in display_item_df.columns:
                display_item_df = display_item_df.rename(
                    columns={"notes": "description"}
                )

            st.dataframe(
                display_item_df,
                use_container_width=True
            )

        else:
            st.info("No item records found.")

    with auec_log_tab:
        if not currency_df.empty:
            display_currency_df = currency_df.copy()

            for column in ["id", "idx"]:
                if column in display_currency_df.columns:
                    display_currency_df = display_currency_df.drop(columns=[column])

            if "amount" in display_currency_df.columns:
                display_currency_df["amount"] = display_currency_df["amount"].apply(
                    lambda amount: f"{int(amount):,}"
                )

            st.dataframe(
                display_currency_df,
                use_container_width=True
            )

        else:
            st.info("No AUEC records found.")
