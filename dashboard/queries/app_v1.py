import streamlit as st
from db_connection import run_query
import plotly.express as px
import altair as alt

st.set_page_config(
    page_title="Olist Dashbaord",
    layout="wide"
)

st.title("Dashboard de Ventas — Olist E-commerce")

# => Ejcutamos las vistas (mestricas)
monthly_sales = run_query("SELECT * FROM analytics.vw_monthly_sales;")
sales_by_state = run_query("SELECT * FROM analytics.vw_sales_by_state;")
category_performance = run_query("SELECT * FROM analytics.vw_category_performance;")
sales_state_month = run_query("SELECT * FROM analytics.vw_sales_states_month;")
payment_behavier = run_query("SELECT * FROM analytics.vw_payment_behavior;")
delivery_performance = run_query("SELECT * FROM analytics.vw_delivery_performance;")

# => Aplicamos comboxes de filtros (ventas, stados y categorias)
st.sidebar.header("Filtros")

available_months = sorted(monthly_sales["purchase_month"].unique())
start_month, final_month = st.sidebar.select_slider(
    "Rango de meses",
    options=available_months,
    value=(available_months[0], available_months[-1]),
)

available_state = sorted(sales_by_state["customer_state"].unique())
selected_state = st.sidebar.multiselect(
    "Estado de clientes",
    options=available_state,
    default=available_state,
)

available_categorys = sorted(category_performance["category_name"].unique())
selected_category = st.sidebar.multiselect(
    "Categoría de producto",
    options=available_categorys,
    default=available_categorys,
)

payment_methods = st.sidebar.multiselect(
    "Métodos de pago",
    options=payment_behavier["payment_method"],
    default=payment_behavier["payment_method"],
)

# => Aplicamos los filtros para las datos

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

# payment_behavier_filtered = 

# => Deginimos indicadores de desarrollo (KPIs) principales

total_revenue = monthly_sales_filtered["total_revenue"].sum()
total_orders = monthly_sales_filtered["total_orders"].sum()
avg_ticket = ( total_revenue / total_orders if total_orders > 0 else 0 )
avg_late_rate = sales_by_state_filtered["late_rate_pct"].mean()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Ingresos totales", f"R$ {total_revenue:,.2f}")
col2.metric("Pedidos totales", f"{total_orders:,.0f}")
col3.metric("Ticket promedio", f"R$ {avg_ticket:,.2f}")
col4.metric("Tasa de retraso promedio", f"{avg_late_rate:.1f}%")

st.divider()

# => Visualizacion de los datos
# st.write("Meses filtrados:", len(monthly_sales_filtered))
# st.write("Estados filtrados:", len(sales_by_state_filtered))
# st.write("Categorías filtradas:", len(category_performance_filtered))

# -- ==============================================================
# => DESARROLLO DE GRAFCIOS

# Grafico 1
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

fg_sales.update_layout(hovermode="x unified")
st.plotly_chart(fg_sales, use_container_width=True)

st.divider()

col_graf_1, col_graf_2 = st.columns(2)

# Grafico 2
with col_graf_1:
    st.subheader("Ventas por estado")

    sales_by_state_sorted = sales_by_state_filtered.sort_values("total_revenue", ascending=True)
    fg_states = px.bar(
        sales_by_state_sorted,
        x="total_revenue",
        y="customer_state",
        orientation="h",
        color="late_rate_pct",
        color_continuous_scale="RdYlGn_r",  # rojo = mala tasa de retraso, verde = buena
        labels={
            "total_revenue": "Ingresos (R$)",
            "customer_state": "Estado",
            "late_rate_pct": "% Retraso",
        }
    )

    fg_states.update_layout(
        coloraxis_colorbar=dict(title="% Retraso")
    )

    st.plotly_chart(fg_states, use_container_width=True)

# Grafico 3
with col_graf_2:
    st.subheader("Rendimiento por categoria de producto")

    fg_categories = px.scatter(
        category_performance_filtered,
        x="total_orders",
        y="avg_review_score",
        size="total_revenue",
        color="avg_review_score",
        color_continuous_scale="RdYlGn",
        hover_name="category_name",
        labels={
            "total_orders": "Cantidad de pedidos",
            "avg_review_score": "Score promedio de reseña",
            "total_revenue": "Ingresos totales",
        },
        size_max=50,
    )

    fg_categories.update_layout(coloraxis_showscale=False)

    st.plotly_chart(fg_categories, use_container_width=True)

# -- ====================================================================

st.divider()

# Grafico 4

st.subheader("Mapa  de calor: Ventas por estado y mes")

heatmap = (
    alt.Chart(sales_state_month_filtered) # Inicio basico para el uso de alatir (alt)
    .mark_rect() #  defionición del tipo de grafico .mark_tipo
    .encode( #  definiciond e variables  (x,y)
        x=alt.X("purchase_month:O", title="Mes"),
        y=alt.Y("customer_state:O", title="Estado", sort="-x"),
        color=alt.Color(
            "total_revenue:Q",
            title="Ingresos (R$)",
            scale=alt.Scale(scheme="yelloworangered"),
        ),
        tooltip=[ # propiedades generales del grafico
            alt.Tooltip("customer_state:N", title="Estado"),
            alt.Tooltip("purchase_month:O", title="Mes"),
            alt.Tooltip("total_revenue:Q", title="Ingresos", format=",.2f"),
        ],
    ).properties(height=500)
)

st.altair_chart(heatmap, use_container_width=True)

st.divider()

col_graf_5, col_graf_6 = st.columns(2)

with col_graf_5:
    st.subheader("Método de pago y financiamiento")

    fg_pay_method = px.pie(
        payment_methods_filtered,
        names="payment_method",
        values="total_orders",
        labels={
            "payment_method": "Método de Pago",
            "total_orders": "Total de Órdenes"
        }
    )

    st.plotly_chart(fg_pay_method, use_container_width=True)

with col_graf_6:
    st.subheader("Rendimiento y tiempos de entrega por estado")

    fg_delivery = px.bar(
        delivery_performance_filtered,
        x="customer_state",
        y=["avg_delivery_days", "avg_buffer_days"],
        labels={
            "customer_state": "Estado",
            "value": "Días Promedio",
            "variable": "Métrica Logística",
            "avg_delivery_days": "Días de Entrega",
            "avg_buffer_days": "Días de Margen (Buffer)",
        },
        barmode="group",
        color_discrete_map={
            "avg_delivery_days": "#3366CC",
            "avg_buffer_days": "#109618",
        },
    )

    fg_delivery.update_layout(
        legend_title_text="Indicador",
        xaxis_title="Estado del Cliente",
        yaxis_title="Días",
    )

    st.plotly_chart(fg_delivery, use_container_width=True)