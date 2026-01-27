import json 
from langchain_core.prompts import ChatPromptTemplate

import os
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# ↑ gets the current directory where this script is located

TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

_jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"])
)

import re
def build_html_table(
    table_columns,
    table_rows,
    columns_metadata
) -> str:
    template = _jinja_env.get_template("table.html")
    html = template.render(
        table_columns=table_columns,
        table_rows=table_rows[:50],
        columns_metadata=columns_metadata or {}
    )

    # --- HARD NORMALIZATION ---
    # 1. Remove newlines and tabs
    html = html.replace("\n", "").replace("\t", "")

    # 2. Collapse multiple spaces into one
    html = re.sub(r"\s{2,}", " ", html)

    # 3. Remove spaces between tags: >   <
    html = re.sub(r">\s+<", "><", html)
    return html.strip()





def build_prompt_v3() -> ChatPromptTemplate:
    system_text = r"""
    You are a **Healthcare Marketing Analytics Summarizer** trained to interpret structured, tabular outputs
    from InsightIQ — a data-driven HCP analytics system.

    Your job: analyze summarized analytical outputs (top 100 rows) and produce a **Markdown summary**.
    
    DATA PRESENTATION RULES:
    1. If the chart type is a GRAPH, output the data as a JSON code block for rendering, followed by the text summary.

    ---

    ## CONTEXT

    ### Subquery
    {{ subquery }}

    ---
    ### Visual Data Output
    {%- if visualization and visualization.chart_type == "TABLE" -%}
    The visualization for this query is a TABLE.
    The table will be rendered externally.
    You must NOT generate any table, HTML, Markdown table, or tabular structure.
    Proceed directly to the analytical summary sections only.

    {%- elif visualization and visualization.chart_type == "MARKETSHARE_GRAPH" -%}
    Provide the data in a JSON code block for plotting.
    Structure:
    ```json
    {
      "plottinggraph": [
        {
          "chartType": "STACKED_BAR",
          "xAxis": ["name"],
          "yAxis": {% if table_rows and table_rows[0].data is defined %}{{ table_rows[0].data | map(attribute='name') | list | tojson }}{% else %}[]{% endif %},
          "chartData": {{ table_text }}
        }
      ]
    }
    ```

    {%- else -%}
    Provide the data in a JSON code block for plotting.
    Structure:
    ```json
    {
      "plottinggraph": [
        {
          "chartType": "BAR",
          "xAxis": [""],
          "yAxis": ["", ""],
          "chartData": {{ table_rows[:100] | tojson(indent=2) }}
        }
      ]
    }
    ```
    {%- endif -%}
    
    ---

    ### Visualization Metadata
    {{ visualization_pretty }}

    ---

    ## RULES OF SUMMARIZATION (Apply to ALL outputs)
    1. **CRITICAL:** If you output a JSON code block above, you **MUST** close it with triple backticks (```) and insert **two blank lines** before starting the "Key Insights" section.
    2. Use **column descriptions** from "Column Metadata" to interpret variables.
    3. Output the summary in **Markdown**.
    4. Derive **insights**, not repetitions of numbers.
    5. Include the following sections in order:
       - **Key Insights** — concise, data-driven points
       - **Business Implication** — brief strategic or marketing interpretation
       - **Executive Summary** — one concise insight sentence
    6. Be concise, clear, and business-focused.

    ## EXPECTED OUTPUT FORMAT
    
    #### The Below information being presented to you is curated from the Real World data avaialble within our exosystem .  

    ### Key Insights
    - Write 2–3 concise insights derived from the data.

    ### Business Implication
    Write 1–2 sentences summarizing marketing or adoption impact.

    ### Executive Summary
    One concise takeaway summarizing the finding.

    <br>
    ---

    ## FINAL FORMATTING RULES
    - Do NOT output any literal "\n" or "\\n" text. Use real newlines only.
    - Ensure the JSON block is completely closed before the Markdown text begins.
    """

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_text),
            (
                "human",
                "Subquery:\n\n{{ subquery }}\n\n"
                "User Preference:\n{{ user_pref | tojson(indent=2) }}\n\n"
                "Table Columns:\n{{ table_columns | tojson(indent=2) }}\n\n"
                "Table Rows:\n{{ table_rows | tojson(indent=2) }}\n\n"
                "Table Text:\n{{ table_text | tojson(indent=2) }}\n\n"
                "Visualization:\n{{ visualization | tojson(indent=2) }}\n\n"
                "Columns Metadata:\n{{ columns_metadata | tojson(indent=2) }}\n\n"
            ),
        ],
        template_format="jinja2",
    )


def render__prompt(
    subquery: str,
    table_text: str,
    visualization: dict | None = None,
    user_pref: dict | None = None,
    table_columns: list | None = None,
    table_rows: list | None = None,
    columns_metadata: dict | None = None,
) -> str:
    visualization = visualization or {}
    user_pref = user_pref or {}

    visualization_pretty = json.dumps(visualization, indent=2, ensure_ascii=False)

    rendered_html = ""
    if visualization.get("chart_type") == "TABLE":
        rendered_html = build_html_table(
            table_columns=table_columns,
            table_rows=table_rows,
            columns_metadata=columns_metadata,
        )

    template = build_prompt_v3()

    formatted = template.format_prompt(
        subquery=subquery or "",
        table_text=table_text or "",
        visualization_pretty=visualization_pretty,
        visualization=visualization,
        user_pref=user_pref,
        table_columns=table_columns or [],
        table_rows=table_rows or [],
        columns_metadata=columns_metadata or {},
        rendered_html="",  # IMPORTANT: DO NOT PASS HTML INTO TEMPLATE
    )

    # 1. Serialize prompt (LLM-safe)
    try:
        prompt_str = formatted.to_string()
        if not prompt_str.strip():
            prompt_str = "\n\n".join([m.content for m in formatted.to_messages()])
    except Exception:
        prompt_str = "\n\n".join([m.content for m in formatted.to_messages()])

    prompt_str = prompt_str.strip()


    return prompt_str,rendered_html
