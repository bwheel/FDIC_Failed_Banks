import os
import sqlite3
import re
from jinja2 import Environment, FileSystemLoader

# Paths
DB_FILE = "fdic_failed_banks.db"
TEMPLATES_DIR = "templates"
OUTPUT_DIR = "docs"
OUTPUT_BANKS_DIR = os.path.join(OUTPUT_DIR, "banks")
OUTPUT_STATES_DIR = os.path.join(OUTPUT_DIR, "states")
ALL_STATES = [
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
]

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_BANKS_DIR, exist_ok=True)
os.makedirs(OUTPUT_STATES_DIR, exist_ok=True)

# Initialize Jinja2
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

# -------------------------------
# Connect to SQLite DB
# -------------------------------
conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# Fetch all states
cur.execute("SELECT DISTINCT state FROM failed_banks")
states = [row[0] for row in cur.fetchall()]

# Fetch all banks
cur.execute("""
    SELECT bank_name, city, state, cert, acquiring_institution, closing_date, fund
    FROM failed_banks
""")
banks_from_db = cur.fetchall()

cur = conn.cursor()
cur.execute("SELECT State, COUNT(*) as count FROM failed_banks GROUP BY State;")
state_counts = dict(cur.fetchall())

# Build dict: {state: [{name, url}, ...]}
state_banks = {}
cur = sqlite3.connect(DB_FILE).cursor()
cur.execute("SELECT State, bank_name FROM failed_banks ORDER BY State, bank_name")
for state, bank_name in cur.fetchall():
    url = re.sub(r"[^a-zA-Z0-9]+", "-", bank_name).strip("-").lower() + ".html"
    state_banks.setdefault(state, []).append({"name": bank_name, "url": f"banks/{url}"})


conn.close()


# -------------------------------
# Page generation helper
# -------------------------------


def save_html(output_path: str, html: str):
    if os.path.exists(output_path) and os.path.isfile(output_path):
        os.remove(output_path)
    print(f"creating: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated {output_path}")


def render_page(output_path, title):
    template = env.get_template("page.html")
    html = template.render(title=title)
    save_html(output_path, html)


def render_index(counts, state_banks):
    """
    Renders index.html with:
    - Datamap of failed banks by state (state_counts)
    - Single-column list of states and banks, alphabetical
    """
    # Sort states alphabetically
    states_sorted = sorted(state_banks.items(), key=lambda x: x[0])

    # Wrap in a single-column list for the template
    columns = [states_sorted]

    # Render template
    template = env.get_template("index.html")
    html = template.render(title="Home", state_counts=counts, columns=columns)

    output_path = os.path.join(OUTPUT_DIR, "index.html")
    save_html(output_path, html)


def render_state_pages(all_states, state_banks_map):
    """
    Generates an HTML page for each state using state.html template.
    """
    template = env.get_template("state.html")  # use state-specific template

    for state in all_states:
        filename = f"{state}.html"
        path = os.path.join(OUTPUT_STATES_DIR, filename)
        banks_list = state_banks_map.get(state, [])
        html = template.render(title=f"State: {state}", state=state, banks=banks_list)
        save_html(path, html)


def render_bank(bank):
    """
    Renders a single bank page using bank.html template.
    `bank` should be a dict with keys:
      name, city, state, cert, acquiring_institution, closing_date, fund
    """
    template = env.get_template("bank.html")
    filename = re.sub(r"[^a-zA-Z0-9]+", "-", bank["name"]).strip("-").lower() + ".html"
    path = os.path.join(OUTPUT_BANKS_DIR, filename)
    html = template.render(title=f"Bank: {bank['name']}", bank=bank)
    save_html(path, html)


# -------------------------------
# Generate static pages
# -------------------------------
render_index(state_counts, state_banks)
render_page(os.path.join(OUTPUT_DIR, "all.html"), "All Banks")
render_page(os.path.join(OUTPUT_DIR, "timeline.html"), "Timeline")


# Ensure state_banks_map contains all states
state_banks_map = {state: [] for state in ALL_STATES}
for state, banks_list in state_banks.items():
    state_banks_map[state] = banks_list

render_state_pages(ALL_STATES, state_banks_map)

# Bank pages
for bank_row in banks_from_db:  # Replace with your DB fetch
    bank = {
        "name": bank_row[0],
        "city": bank_row[1],
        "state": bank_row[2],
        "cert": bank_row[3],
        "acquiring_institution": bank_row[4],
        "closing_date": bank_row[5],
        "fund": bank_row[6],
    }
    render_bank(bank)
