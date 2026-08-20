import streamlit as st
from db_connection import run_query
import plotly.express as px
import altair as alt

st.set_page_config(page_title="Olist Dashboard", layout="wide", page_icon="▰")

BG = "#0B0D10"
CARD = "#15191F"
CARD_2 = "#11151A"
BORDER = "#2A3038"
YELLOW = "#F2B84B"
ORANGE = "#E8752E"
RED = "#D94A4A"
TEXT = "#F4F4F5"
MUTED = "#9CA3AF"

st.markdown(f"""
<style>
.stApp {{
    background: {BG};
    color: {TEXT};
}}
.block-container {{
    padding-top: 1.4rem;
    padding-bottom: 1.5rem;
    max-width: 1600px;
}}
h1 {{
    color: {TEXT} !important;
    font-weight: 750 !important;
    letter-spacing: -0.7px;
    margin-bottom: 0.2rem !important;
}}
h2, h3 {{
    color: {TEXT} !important;
    font-weight: 650 !important;
    letter-spacing: -0.25px;
}}
section[data-testid="stSidebar"] {{
    background: #0E1116 !important;
    border-right: 1px solid {BORDER};
}}
section[data-testid="stSidebar"] > div {{
    padding-top: 1.2rem;
}}
section[data-testid="stSidebar"] h2 {{
    color: {TEXT} !important;
}}
section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {CARD_2} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 14px !important;
    padding: 5px 10px !important;
}}
section[data-testid="stSidebar"] label {{
    color: {TEXT} !important;
    font-weight: 500 !important;
}}
div[data-testid="stMetric"] {{
    background: linear-gradient(145deg, {CARD}, #12151A);
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 17px 18px;
    min-height: 105px;
    transition: border-color 0.2s ease, transform 0.2s ease;
}}
div[data-testid="stMetric"]:hover {{
    border-color: {ORANGE};
    transform: translateY(-2px);
}}
div[data-testid="stMetricLabel"] {{
    color: {MUTED} !important;
}}
div[data-testid="stMetricValue"] {{
    color: {TEXT} !important;
    font-weight: 700 !important;
}}
div[data-testid="stMetric"]:nth-of-type(1) div[data-testid="stMetricValue"] {{
    color: {YELLOW} !important;
}}
hr {{
    margin-top: 0.7rem !important;
    margin-bottom: 0.7rem !important;
    border-color: {BORDER} !important;
}}
div[data-testid="stPlotlyChart"] {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 4px;
}}
div[data-testid="stVegaLiteChart"] {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 8px;
}}
.stMultiSelect span[data-baseweb="tag"] {{
    background-color: {ORANGE} !important;
    color: white !important;
}}
</style>
""", unsafe_allow_html=True)

st.title("Dashboard de Ventas — Olist E-commerce")

monthly_sales = run_query("SELECT * FROM analytics.vw_monthly_sales;")
sales_by_state = run_query("SELECT * FROM analytics.vw_sales_by_state;")
category_performance = run_query("SELECT * FROM analytics.vw_category_performance;")
sales_state_month = run_query("SELECT * FROM analytics.vw_sales_states_month;")
payment_behavier = run_query("SELECT * FROM analytics.vw_payment_behavior;")
delivery_performance = run_query("SELECT * FROM analytics.vw_delivery_performance;")

st.sidebar.header("Filtros")

available_months = sorted(monthly_sales["purchase_month"].unique())
with st.sidebar.container(border=True):
    start_month, final_month = st.select_slider(
        "Rango de meses",
        options=available_months,
        value=(available_months[0], available_months[-1])
    )

available_state = sorted(sales_by_state["customer_state"].unique())
with st.sidebar.container(border=True):
    selected_state = st.multiselect(
        "Estado de clientes",
        options=available_state,
        default=available_state
    )

available_categorys = sorted(category_performance["category_name"].unique())
with st.sidebar.container(border=True):
    selected_category = st.multiselect(
        "Categoría de producto",
        options=available_categorys,
        default=available_categorys
    )

available_payment_methods = sorted(payment_behavier["payment_method"].unique())
with st.sidebar.container(border=True):
    payment_methods = st.multiselect(
        "Métodos de pago",
        options=available_payment_methods,
        default=available_payment_methods
    )

monthly_sales_filtered = monthly_sales[
    (monthly_sales["purchase_month"] >= start_month)
    & (monthly_sales["purchase_month"] <= final_month)
]
sales_by_state_filtered = sales_by_state[
    sales_by_state["customer_state"].isin(selected_state)
]
category_performance_filtered = category_performance[
    category_performance["category_name"].isin(selected_category)
]
sales_state_month_filtered = sales_state_month[
    (sales_state_month["customer_state"].isin(selected_state))
    & (sales_state_month["purchase_month"] >= start_month)
    & (sales_state_month["purchase_month"] <= final_month)
]
payment_methods_filtered = payment_behavier[
    payment_behavier["payment_method"].isin(payment_methods)
]
delivery_performance_filtered = delivery_performance[
    delivery_performance["customer_state"].isin(selected_state)
]

total_revenue = monthly_sales_filtered["total_revenue"].sum()
total_orders = monthly_sales_filtered["total_orders"].sum()
avg_ticket = total_revenue / total_orders if total_orders > 0 else 0
avg_late_rate = sales_by_state_filtered["late_rate_pct"].mean()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Ingresos totales", f"R$ {total_revenue:,.2f}")
col2.metric("Pedidos totales", f"{total_orders:,.0f}")
col3.metric("Ticket promedio", f"R$ {avg_ticket:,.2f}")
col4.metric("Tasa de retraso promedio", f"{avg_late_rate:.1f}%")

def plotly_style(fig, height=390):
    fig.update_layout(
        height=height,
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,
        font=dict(color=TEXT, family="Arial"),
        margin=dict(l=35, r=25, t=25, b=35),
        xaxis=dict(
            gridcolor="#252A31",
            linecolor=BORDER,
            tickfont=dict(color=MUTED),
            title_font=dict(color=MUTED)
        ),
        yaxis=dict(
            gridcolor="#252A31",
            linecolor=BORDER,
            tickfont=dict(color=MUTED),
            title_font=dict(color=MUTED)
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=MUTED)
        ),
        hoverlabel=dict(
            bgcolor="#20252C",
            font_color=TEXT,
            bordercolor=BORDER
        )
    )
    return fig

st.divider()
st.subheader("Evolución de ventas mensuales")

fg_sales = px.line(
    monthly_sales_filtered,
    x="purchase_month",
    y="total_revenue",
    markers=True,
    labels={
        "purchase_month": "Mes",
        "total_revenue": "Ingresos (R$)"
    }
)
fg_sales.update_traces(
    line=dict(color=ORANGE, width=3),
    marker=dict(color=YELLOW, size=8, line=dict(color=BG, width=2)),
    fill="tozeroy",
    fillcolor="rgba(232,117,46,0.08)"
)

fg_sales.update_layout(hovermode="x unified")
plotly_style(fg_sales, 370)
st.plotly_chart(fg_sales, use_container_width=True)

st.divider()
col_graf_1, col_graf_2 = st.columns(2, gap="medium")

with col_graf_1:
    st.subheader("Ventas por estado")
    sales_by_state_sorted = sales_by_state_filtered.sort_values(
        "total_revenue",
        ascending=True
    )
    fg_states = px.bar(
        sales_by_state_sorted,
        x="total_revenue",
        y="customer_state",
        orientation="h",
        color="late_rate_pct",
        color_continuous_scale=[
            [0, YELLOW],
            [0.5, ORANGE],
            [1, RED]
        ],
        labels={
            "total_revenue": "Ingresos (R$)",
            "customer_state": "Estado",
            "late_rate_pct": "% Retraso"
        }
    )
    fg_states.update_layout(
        coloraxis_colorbar=dict(
            title="% Retraso",
            tickfont=dict(color=MUTED),
            title_font=dict(color=MUTED)
        )
    )

    fg_states.update_traces(marker_line_width=0)
    plotly_style(fg_states, 430)
    st.plotly_chart(fg_states, use_container_width=True)

with col_graf_2:
    st.subheader("Rendimiento por categoría")

    fg_categories = px.scatter(
        category_performance_filtered,
        x="total_orders",
        y="avg_review_score",
        size="total_revenue",
        color="avg_review_score",
        color_continuous_scale=[
            [0, RED],
            [0.5, ORANGE],
            [1, YELLOW]
        ],
        hover_name="category_name",
        labels={
            "total_orders": "Cantidad de pedidos",
            "avg_review_score": "Score promedio",
            "total_revenue": "Ingresos totales"
        },
        size_max=48
    )
    fg_categories.update_traces(
        marker=dict(
            opacity=0.82,
            line=dict(width=1, color="#E8E8E8")
        )
    )

    fg_categories.update_layout(coloraxis_showscale=False)
    plotly_style(fg_categories, 430)
    st.plotly_chart(fg_categories, use_container_width=True)

st.divider()
st.subheader("Mapa de calor — Ventas por estado y mes")

heatmap = (
    alt.Chart(sales_state_month_filtered)
    .mark_rect(cornerRadius=2)
    .encode(
        x=alt.X(
            "purchase_month:O",
            title="Mes",
            axis=alt.Axis(labelColor=MUTED, titleColor=MUTED)
        ),
        y=alt.Y(
            "customer_state:O",
            title="Estado",
            sort="-x",
            axis=alt.Axis(labelColor=MUTED, titleColor=MUTED)
        ),
        color=alt.Color(
            "total_revenue:Q",
            title="Ingresos (R$)",
            scale=alt.Scale(
                range=["#2A1A12", ORANGE, YELLOW]
            ),
            legend=alt.Legend(
                labelColor=MUTED,
                titleColor=MUTED
            )
        ),
        tooltip=[
            alt.Tooltip("customer_state:N", title="Estado"),
            alt.Tooltip("purchase_month:O", title="Mes"),
            alt.Tooltip("total_revenue:Q", title="Ingresos", format=",.2f")
        ]
    )
    .properties(height=430)
    .configure_view(strokeOpacity=0)
    .configure(background=CARD)
)

st.altair_chart(heatmap, use_container_width=True)

st.divider()
col_graf_5, col_graf_6 = st.columns(2, gap="medium")

with col_graf_5:
    st.subheader("Método de pago")

    fg_pay_method = px.pie(
        payment_methods_filtered,
        names="payment_method",
        values="total_orders",
        hole=0.52,
        color_discrete_sequence=[
            YELLOW,
            ORANGE,
            RED,
            "#C45F32",
            "#D99A3D"
        ],
        labels={
            "payment_method": "Método de Pago",
            "total_orders": "Total de Órdenes"
        }
    )
    fg_pay_method.update_traces(
        textposition="inside",
        textinfo="percent",
        marker=dict(
            line=dict(color=CARD, width=3)
        )
    )

    plotly_style(fg_pay_method, 420)
    fg_pay_method.update_layout(
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
            title=None,
            font=dict(
                size=13,
                color=TEXT
            )
        ),
        annotations=[
            dict(
                text="Pagos",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=17, color=TEXT)
            )
        ],
        margin=dict(l=20, r=130, t=20, b=20)
    )

    st.plotly_chart(fg_pay_method, use_container_width=True)

with col_graf_6:
    st.subheader("Rendimiento de entregas")
    fg_delivery = px.bar(
        delivery_performance_filtered,
        x="customer_state",
        y=["avg_delivery_days", "avg_buffer_days"],
        barmode="group",
        color_discrete_map={
            "avg_delivery_days": ORANGE,
            "avg_buffer_days": YELLOW
        },
        labels={
            "customer_state": "Estado",
            "value": "Días promedio",
            "variable": "Indicador",
            "avg_delivery_days": "Días de entrega",
            "avg_buffer_days": "Margen estimado"
        }
    )
    fg_delivery.update_traces(marker_line_width=0)
    fg_delivery.update_layout(
        legend_title_text="Indicador",
        xaxis_title="Estado",
        yaxis_title="Días"
    )

    plotly_style(fg_delivery, 420)
    st.plotly_chart(fg_delivery, use_container_width=True)