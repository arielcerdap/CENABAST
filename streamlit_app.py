import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# Función para formatear números con abreviaciones
def format_number(x):
    if x == 0:
        return '0'
    
    x = int(x)
    if x >= 1000000:
        return f'{x/1000000:.0f}M'
    elif x >= 1000:
        return f'{x/1000:.0f}k'
    else:
        return f'{x}'

# Función para formatear valores monetarios
def format_currency(value):
    return f"{value:,.0f}".replace(",", "@").replace(".", ",").replace("@", ".")

# Cargar los datos
@st.cache_data
def load_data():
    file_path = 'datos_cenabast.xlsx'
    data = pd.read_excel(file_path, sheet_name='Sheet 1')
    return data

data = load_data()

# Convertir las fechas y limpiar datos
data['Fecha de compra'] = pd.to_datetime(data['Fecha de compra'], errors='coerce')
data['Año'] = data['Fecha de compra'].dt.year
data['Mes'] = data['Fecha de compra'].dt.month
data['Día'] = data['Fecha de compra'].dt.day

# Evitar errores en cálculos dividiendo entre 0
data['Cantidad unitaria'] = data['Cantidad unitaria'].replace(0, 1)
data['Monto total'] = pd.to_numeric(data['Monto total'], errors='coerce')
data['Cantidad unitaria'] = pd.to_numeric(data['Cantidad unitaria'], errors='coerce')
data['Precio promedio'] = data['Monto total'] / data['Cantidad unitaria']

# Rango completo de años
años_completos = pd.DataFrame({'Año': range(data['Año'].min(), data['Año'].max() + 1)})

# Títulos del dashboard
st.title("🏥 Dashboard de Compras de Productos por CENABAST")
st.markdown("Este dashboard permite visualizar las compras de productos a lo largo del tiempo.")
st.markdown("Datos obtenidos desde [CENABAST](https://www.cenabast.cl/compras-cenabast/)")
st.markdown("Fecha actualización reporte: 04-12-2024")
st.markdown("Información actualizada a noviembre del 2024")
st.markdown("Creado por [Ariel Cerda](https://x.com/arielcerdap)")
st.markdown("---")

# Filtro
producto = st.selectbox("Selecciona un producto:", options=data['Nombre producto genérico'].unique())

# Filtrar los datos
df_filtered = data[data['Nombre producto genérico'] == producto]

# Gráfico 1: Gráfico combinado (Monto Total y Cantidad Comprada)
df_grouped = df_filtered.groupby('Año', as_index=False).agg({
    'Monto total': 'sum',
    'Cantidad unitaria': 'sum'
})
df_grouped = años_completos.merge(df_grouped, on='Año', how='left').fillna(0)

# Crear gráfico combinado
fig = go.Figure()

# Generar ticks personalizados para el eje Y1 (Monto total)
max_monto = df_grouped['Monto total'].max()
y1_ticks = np.linspace(0, max_monto, 6)

# Generar ticks personalizados para el eje Y2 (Cantidad unitaria)
max_cantidad = df_grouped['Cantidad unitaria'].max()
y2_ticks = np.linspace(0, max_cantidad, 6)

# Agregar barras para "Monto Total"
fig.add_trace(go.Bar(
    x=df_grouped['Año'],
    y=df_grouped['Monto total'],
    name='Monto Total',
    marker_color='#3498DB',
    yaxis='y1',
    text=[format_number(x) for x in df_grouped['Monto total']],
    textposition='inside',
    insidetextfont=dict(color='white')
))

# Agregar línea para "Cantidad Unitaria"
fig.add_trace(go.Scatter(
    x=df_grouped['Año'],
    y=df_grouped['Cantidad unitaria'],
    name='Cantidad Unitaria',
    mode='lines+markers',
    line=dict(color='#F1C40F', width=2),
    yaxis='y2',
    text=[format_number(x) for x in df_grouped['Cantidad unitaria']],
    textposition='top center'
))

# Configurar ejes con ticks personalizados
fig.update_layout(
    title='Monto Total y Cantidad Comprada por Año',
    xaxis=dict(
        title='Año',
        dtick=1,
        type='category'
    ),
    yaxis=dict(
        title='Monto Total (CLP)',
        titlefont=dict(color='#3498DB'),
        tickfont=dict(color='#3498DB'),
        tickmode='array',
        tickvals=y1_ticks,
        ticktext=[format_number(x) for x in y1_ticks],
        ticksuffix=" CLP",
        range=[0, max_monto * 1.1]
    ),
    yaxis2=dict(
        title='Cantidad Unitaria',
        titlefont=dict(color='#F1C40F'),
        tickfont=dict(color='#F1C40F'),
        overlaying='y',
        side='right',
        tickmode='array',
        tickvals=y2_ticks,
        ticktext=[format_number(x) for x in y2_ticks],
        range=[0, max_cantidad * 1.1]
    ),
    legend=dict(x=0.5, y=-0.2, orientation='h'),
    barmode='group',
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
)

# Añadir líneas de cuadrícula
fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

st.plotly_chart(fig)

# Gráfico 2: Distribución de compras por empresa (Gráfico de torta)
grafico_torta = px.pie(
    df_filtered,
    names='Proveedor',
    values='Monto total',
    title='Distribución de Compras por Empresa',
    color_discrete_sequence=px.colors.qualitative.Set3
)

grafico_torta.update_traces(
    texttemplate='%{percent:.1%}',
    hovertemplate='%{label}<br>Monto: ' + '%{value:,.0f} CLP<br>%{percent:.1%}'
)

grafico_torta.update_layout(
    paper_bgcolor='rgba(0,0,0,0)'
)

st.plotly_chart(grafico_torta)

# Gráfico 3: Precios promedio por año (Gráfico de barras laterales)
df_precios = df_filtered.groupby('Año', as_index=False).agg({
    'Precio promedio': 'mean'
})
df_precios = años_completos.merge(df_precios, on='Año', how='left').fillna(0)

fig_precios = px.bar(
    df_precios,
    x='Año',
    y='Precio promedio',
    title='Precios Promedio por Año',
    labels={'Precio promedio': 'Precio Promedio (CLP)'}
)

# Generar ticks personalizados para el eje Y
max_precio = df_precios['Precio promedio'].max()
precio_ticks = np.linspace(0, max_precio, 6)

fig_precios.update_traces(
    text=[format_number(x) for x in df_precios['Precio promedio']],
    textposition='inside',
    marker_color='#2E86C1',
    insidetextfont=dict(color='white')
)

fig_precios.update_layout(
    xaxis=dict(
        dtick=1,
        type='category'
    ),
    yaxis=dict(
        tickmode='array',
        tickvals=precio_ticks,
        ticktext=[format_number(x) for x in precio_ticks]
    ),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)'
)

fig_precios.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
fig_precios.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

st.plotly_chart(fig_precios)