# toy_dash_app.py project:
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, ctx
import plotly.express as px
import dash_bootstrap_components as dbc

# load the data as toys_df to read the data and init it as a data frame:
toys_df = pd.read_csv("./data/toy-sales.csv")

# Precompute dropdown options so that unique values are held [East, West, North, South]!
unique_regions = sorted(toys_df["region"].unique())
region_menu_options = [{"label": r, "value": r} for r in unique_regions]

# * Init the app to Dash and bootstrapt it: (LUX is elegant seems to be more elegant solution of a theme)
app = Dash(__name__, external_stylesheets=[dbc.themes.LUX])
app.title = "Toy Sales Analytics"

# Helper fucntions of formating extra decimals and some numbers for cleaner look:
def fmt_currency(x):
    try:
        return f"${x:,.0f}"
    except Exception:
        return "-"

def fmt_number(x):
    try:
        return f"{x:,.1f}"
    except Exception:
        return "-"

# Navbar with embedded filters so selections stay visible
navbar_filters = html.Div(
    [
        html.Div(
            [
                dbc.Label(
                    "Select region(s):",
                    html_for="region-menu",
                    className="text-muted small mb-1",
                ),
                dcc.Dropdown(
                    id="region-menu",
                    options=region_menu_options,
                    value=unique_regions,
                    multi=True,
                    clearable=True,
                    searchable=True,
                    placeholder="Choose regions...",
                    style={"minWidth": "220px"},
                ),
            ],
            className="d-flex flex-column flex-grow-1",
            style={"minWidth": "220px", "maxWidth": "380px"},
        ),
        html.Div(
            [
                dbc.Label(
                    "Line aggregation",
                    className="text-muted small mb-1",
                ),
                dcc.RadioItems(
                    id="line-mode",
                    options=[
                        {"label": " Total", "value": "total"},
                        {"label": " By Region", "value": "region"},
                        {"label": " By Product", "value": "product"},
                    ],
                    value="total",
                    inputStyle={"marginRight": "6px"},
                    labelStyle={"marginRight": "18px"},
                    inline=True,
                ),
            ],
            className="d-flex flex-column flex-grow-1",
            style={"minWidth": "240px"},
        ),
        html.Div(
            [
                dbc.Button("Clear All", id="clear-btn", color="danger", size="sm"),
                dbc.Button("Select All", id="select-btn", color="success", size="sm"),
            ],
            className="d-flex align-items-end gap-2",
        ),
    ],
    className="d-flex flex-wrap align-items-end gap-3 w-100",
)

navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.H3(
                                    "Toy Sales Dashboard", className="mb-0 fw-bold"
                                ),
                                html.Small(
                                    "data visual analytics", className="text-muted"
                                ),
                            ]
                        ),
                        xs="auto",
                        className="me-md-4",
                    ),
                    dbc.Col(navbar_filters, className="flex-grow-1"),
                ],
                align="center",
                className="g-3 flex-wrap flex-md-nowrap w-100",
            ),
        ],
        fluid=True,
    ),
    color="white",
    class_name="border-bottom shadow-sm py-2",
    sticky="top",
)

# kpi cards,
def kpi_card(id_value, label, color="primary"):
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(label, className="text-muted small"),
                html.H4(id=id_value, className=f"mb-0 fw-bold text-{color}"),
            ]
        ),
        className="shadow-sm rounded-3 h-100",
    )

kpi_row = dbc.Row(
    [
        dbc.Col(kpi_card("kpi-revenue", "Total Revenue", "success"), md=4, xs=12),
        dbc.Col(kpi_card("kpi-units", "Average Units / Order", "info"), md=4, xs=12),
        dbc.Col(kpi_card("kpi-orders", "Orders (Rows)", "secondary"), md=4, xs=12),
    ],
    className="g-3 mt-4",
)

# chart cards
def chart_card(title, graph_id):
    return dbc.Card(
        [
            dbc.CardHeader(html.H5(title, className="mb-0")),
            dbc.CardBody(
                dcc.Graph(id=graph_id, figure={}, config={"displayModeBar": False})
            ),
        ],
        className="shadow-sm rounded-3 h-100",
    )

line_card = chart_card("Weekly Revenue Over Time", "line-chart")
bar_card = chart_card("Average Units by Product", "bar-chart")
heatmap_card = chart_card("Revenue by Region × Product", "heatmap")

# main layout of the app
app.layout = html.Div(
    [
        navbar,
        dbc.Container(
            [
                # KPI row
                kpi_row,
                # Charts in a grid format: line will take the whole width but the bar and heat map is half by half in the bottom.
                dbc.Row(
                    [
                        dbc.Col(line_card, md=12, className="mt-4"),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(bar_card, md=6, className="mt-4"),
                        dbc.Col(heatmap_card, md=6, className="mt-4"),
                    ]
                ),
                # Footer of the site:
                html.Footer(
                    [
                        html.Hr(),
                        html.P(
                            "© by Nuraly Soltonbekov, 2025 Data Vis",
                            className="text-muted small",
                        ),
                    ],
                    className="mt-4 mb-4",
                ),
            ],
            fluid=True,
        ),
    ]
)


# * all of the needed callback functions of the @app.
@app.callback(
    Output("kpi-revenue", "children"),
    Output("kpi-units", "children"),
    Output("kpi-orders", "children"),
    Output("line-chart", "figure"),
    Output("bar-chart", "figure"),
    Output("heatmap", "figure"),
    Input("region-menu", "value"),
    Input("line-mode", "value"),
)
def update_figs(selected_regions, line_mode):
    # guard
    if not selected_regions:
        dff = toys_df.iloc[0:0].copy()
    else:
        dff = toys_df[toys_df["region"].isin(selected_regions)].copy()

    # KPIs
    total_revenue = dff["revenue"].sum() if not dff.empty else 0
    avg_units = dff["units"].mean() if not dff.empty else 0
    orders_count = len(dff)

    # Line Chart 
    if dff.empty:
        rev_by_date_df = pd.DataFrame(
            {"date": [], "revenue": [], "region": [], "product": []}
        )
    else:
        rev_by_date_df = (
            dff.groupby(["date", "region", "product"], as_index=False)["revenue"].sum()
            .sort_values(by="date")
        )

    if line_mode == "region":
        plot_df = (
            rev_by_date_df.groupby(["date", "region"], as_index=False)["revenue"].sum()
        )
        line_fig = px.line(
            plot_df,
            x="date",
            y="revenue",
            color="region",
            markers=True,
            labels={
                "date": "Date (2023) Weekly",
                "revenue": "Revenue ($)",
                "region": "Region",
            },
            title="Weekly Revenue by Region",
        )
    elif line_mode == "product":
        plot_df = (
            rev_by_date_df.groupby(["date", "product"], as_index=False)["revenue"].sum()
        )
        line_fig = px.line(
            plot_df,
            x="date",
            y="revenue",
            color="product",
            markers=True,
            labels={
                "date": "Date (2023) Weekly",
                "revenue": "Revenue ($)",
                "product": "Product",
            },
            title="Weekly Revenue by Product",
        )
    else:
        plot_df = rev_by_date_df.groupby("date", as_index=False)["revenue"].sum()
        line_fig = px.line(
            plot_df,
            x="date",
            y="revenue",
            markers=True,
            labels={"date": "Date (2023) Weekly", "revenue": "Revenue ($)"},
            title="Weekly Revenue (Total)",
        )

    line_fig.update_layout(
        margin=dict(l=40, r=20, t=50, b=40),
        yaxis_tickprefix="$",
        yaxis_separatethousands=True,
        template="simple_white",
    )

    # Bar chart data
    if dff.empty:
        units_by_product_df = pd.DataFrame({"product": [], "units": []})
    else:
        units_by_product_df = (
            dff.groupby("product", as_index=False)["units"]
            .mean()
            .sort_values(by="units", ascending=False)
        )

    bar_fig = px.bar(
        units_by_product_df,
        x="product",
        y="units",
        color="units",
        color_continuous_scale=px.colors.diverging.RdBu,
        text="units",
        labels={"product": "Product", "units": "Average Units"},
        title="Average Units by Product",
    )
    bar_fig.update_traces(
        texttemplate="%{text:.1f}",
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Units: %{y:.1f}<extra></extra>",
    )
    bar_fig.update_layout(
        margin=dict(l=40, r=20, t=50, b=80),
        yaxis=dict(showgrid=True, zeroline=False),
        coloraxis_showscale=False,
        template="simple_white",
    )

    # Heatmap data
    if dff.empty:
        heatmap_pivoted_df = pd.DataFrame([[0]], index=["-"], columns=["-"])
    else:
        heatmap_df = dff.groupby(["region", "product"], as_index=False)["revenue"].sum()
        heatmap_pivoted_df = heatmap_df.pivot(
            index="region", columns="product", values="revenue"
        ).fillna(0)

    heatmap_fig = px.imshow(
        heatmap_pivoted_df,
        text_auto=True,
        color_continuous_scale=px.colors.sequential.Blues[::-1],
        aspect="auto",
        labels=dict(x=" ", y="Region", color="Revenue ($)"),
        title="Revenue by Region & Product",
    )
    heatmap_fig.update_layout(
        margin=dict(l=60, r=40, t=60, b=60),
        xaxis=dict(side="top", tickfont=dict(size=11), automargin=True),
        yaxis=dict(tickmode="linear", tickfont=dict(size=11), automargin=True),
        coloraxis_colorbar=dict(
            title="Revenue ($)",
            tickprefix="$",
            separatethousands=True,
            title_font=dict(size=12),
            tickfont=dict(size=11),
        ),
        template="simple_white",
    )
    heatmap_fig.update_traces(texttemplate="%{z:,.0f}", textfont=dict(size=12))

    return (
        fmt_currency(total_revenue),
        fmt_number(avg_units),
        f"{orders_count:,}",
        line_fig,
        bar_fig,
        heatmap_fig,
    )


# Buttons to clear and select with @callbacks:
@app.callback(
    Output("region-menu", "value"),
    Input("clear-btn", "n_clicks"),
    Input("select-btn", "n_clicks"),
    State("region-menu", "value"),
    prevent_initial_call=True,
)
def update_region_selection(clear_clicks, select_clicks, current_value):
    triggered = ctx.triggered_id
    if triggered == "clear-btn":
        return []
    if triggered == "select-btn":
        return unique_regions
    return current_value


# Run the app:
if __name__ == "__main__":
    app.run(debug=True)
