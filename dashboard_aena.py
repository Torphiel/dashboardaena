import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime, timedelta
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Licitaciones AENA",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2d5a87 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f4e79;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
</style>
""", unsafe_allow_html=True)

def cargar_datos():
    """Cargar datos de licitaciones desde archivo Excel"""
    try:
        excel_file = "Data_licitaciones/2024_AENA.xlsx"
        if os.path.exists(excel_file):
            df = pd.read_excel(excel_file)
            
            # Mantener las columnas originales del Excel y crear columnas adicionales para el dashboard
            df_processed = df.copy()
            
            # Crear columnas adicionales para compatibilidad con el dashboard
            if 'Clasificación' in df_processed.columns:
                df_processed['Tipo_Obra'] = df_processed['Clasificación']
            if 'Adjudicatario licitación/lote' in df_processed.columns:
                df_processed['Empresa_Adjudicataria'] = df_processed['Adjudicatario licitación/lote']
            if 'Presupuesto base sin impuestos' in df_processed.columns:
                df_processed['Presupuesto_Base'] = df_processed['Presupuesto base sin impuestos']
            if 'Importe adjudicación sin impuestos licitación/lote' in df_processed.columns:
                df_processed['Importe_Adjudicado'] = df_processed['Importe adjudicación sin impuestos licitación/lote']
            if 'Fecha presentación licitación' in df_processed.columns:
                df_processed['Fecha_Publicacion'] = df_processed['Fecha presentación licitación']
            if '%baja' in df_processed.columns:
                df_processed['Porcentaje_Baja'] = df_processed['%baja']
            
            # Limpiar y procesar los datos
            df_processed = procesar_datos(df_processed)
            
            return df_processed
        else:
            st.error(f"Archivo no encontrado: {excel_file}")
            return None
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return None

def procesar_datos(df):
    """Procesar y limpiar los datos del Excel"""
    try:
        # Convertir fecha a datetime
        if 'Fecha_Publicacion' in df.columns:
            df['Fecha_Publicacion'] = pd.to_datetime(df['Fecha_Publicacion'], errors='coerce')
        
        # Limpiar valores nulos en columnas numéricas
        numeric_columns = ['Presupuesto_Base', 'Importe_Adjudicado', 'Porcentaje_Baja']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Procesar porcentaje de baja (multiplicar por 100 para obtener porcentaje real)
        if 'Porcentaje_Baja' in df.columns:
            df['Porcentaje_Baja'] = df['Porcentaje_Baja'] * 100
        
        # Calcular ahorro absoluto
        if 'Presupuesto_Base' in df.columns and 'Importe_Adjudicado' in df.columns:
            df['Ahorro'] = df['Presupuesto_Base'] - df['Importe_Adjudicado']
        
        # Agregar columnas de mes y trimestre
        if 'Fecha_Publicacion' in df.columns:
            df['Mes'] = df['Fecha_Publicacion'].dt.month
            df['Trimestre'] = df['Fecha_Publicacion'].dt.quarter
        
        # Limpiar valores nulos en columnas de texto
        text_columns = ['Aeropuerto', 'Tipo_Obra', 'Empresa_Adjudicataria', 'Estado']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].fillna('No especificado')
        
        # Eliminar filas con datos críticos faltantes
        df = df.dropna(subset=['Aeropuerto', 'Presupuesto_Base'])
        
        return df
    except Exception as e:
        st.error(f"Error al procesar datos: {e}")
        return df

def mostrar_tabla_detallada(df):
    """Mostrar tabla detallada de licitaciones como el Excel con búsqueda"""
    st.subheader("📊 Datos Detallados")
    
    # Crear una copia del DataFrame para mostrar
    df_mostrar = df.copy()
    
    # Usar las columnas exactas del Excel (omitir Estado y Órgano de Contratación)
    columnas_mostrar = [
        'Link licitación',
        'Aeropuerto', 
        'Número de expediente',
        'Objeto del Contrato',
        'Presupuesto base sin impuestos',
        'Fecha presentación licitación',
        'Adjudicatario licitación/lote',
        'Importe adjudicación sin impuestos licitación/lote',
        '%baja',
        'Clasificación'
    ]
    
    # Filtrar solo las columnas que existen
    columnas_existentes = [col for col in columnas_mostrar if col in df_mostrar.columns]
    df_tabla = df_mostrar[columnas_existentes].copy()
    
    # Formatear la columna de porcentaje de baja (multiplicar por 100 para mostrar como porcentaje)
    if '%baja' in df_tabla.columns:
        df_tabla['%baja'] = df_tabla['%baja'].apply(lambda x: f"{x*100:.2f}%")
    
    # Formatear números con separadores de miles
    if 'Presupuesto base sin impuestos' in df_tabla.columns:
        df_tabla['Presupuesto base sin impuestos'] = df_tabla['Presupuesto base sin impuestos'].apply(lambda x: f"{x:,.2f}€")
    if 'Importe adjudicación sin impuestos licitación/lote' in df_tabla.columns:
        df_tabla['Importe adjudicación sin impuestos licitación/lote'] = df_tabla['Importe adjudicación sin impuestos licitación/lote'].apply(lambda x: f"{x:,.2f}€")
    
    # Formatear fechas correctamente
    if 'Fecha presentación licitación' in df_tabla.columns:
        df_tabla['Fecha presentación licitación'] = df_tabla['Fecha presentación licitación'].dt.strftime('%d/%m/%Y')
    
    # Mantener el link completo sin modificar
    if 'Link licitación' in df_tabla.columns:
        # Mantener el link original para que se vea completo
        df_tabla['Link licitación'] = df_tabla['Link licitación'].apply(
            lambda x: str(x) if pd.notna(x) and str(x).strip() != '' else ''
        )
    
    # Buscador
    st.subheader("🔍 Buscar Licitación")
    busqueda = st.text_input(
        "Buscar por aeropuerto, empresa, tipo de obra, número de expediente, etc.:",
        placeholder="Ej: Madrid, Ferrovial, Obras, 2024..."
    )
    
    # Filtrar datos según la búsqueda
    if busqueda:
        # Crear máscara para búsqueda en todas las columnas de texto
        mask = df_tabla.astype(str).apply(lambda x: x.str.contains(busqueda, case=False, na=False)).any(axis=1)
        df_filtrado = df_tabla[mask]
        st.info(f"📊 Mostrando {len(df_filtrado)} resultados de {len(df_tabla)} licitaciones")
    else:
        df_filtrado = df_tabla
        st.info(f"📊 Mostrando todas las {len(df_tabla)} licitaciones")
    
    # Mostrar información sobre las columnas
    st.write(f"**Columnas mostradas:** {', '.join(df_filtrado.columns.tolist())}")
    
    # Mostrar la tabla usando st.dataframe (más confiable)
    st.markdown("""
    <div style="
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px;
        background-color: #fafafa;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
    """, unsafe_allow_html=True)
    
    # Mostrar la tabla con st.dataframe
    st.dataframe(
        df_filtrado,
        use_container_width=True,
        height=600,
        hide_index=True,
        column_config={
            "Link licitación": st.column_config.TextColumn(
                "Link licitación",
                help="URL completa de la licitación",
                width="large"
            ),
            "Aeropuerto": st.column_config.TextColumn(
                "Aeropuerto",
                width="medium"
            ),
            "Número de expediente": st.column_config.TextColumn(
                "Número de expediente",
                width="medium"
            ),
            "Objeto del Contrato": st.column_config.TextColumn(
                "Objeto del Contrato",
                width="large"
            ),
            "Presupuesto base sin impuestos": st.column_config.TextColumn(
                "Presupuesto base sin impuestos",
                width="medium"
            ),
            "Fecha presentación licitación": st.column_config.TextColumn(
                "Fecha presentación licitación",
                width="medium"
            ),
            "Adjudicatario licitación/lote": st.column_config.TextColumn(
                "Adjudicatario licitación/lote",
                width="large"
            ),
            "Importe adjudicación sin impuestos licitación/lote": st.column_config.TextColumn(
                "Importe adjudicación sin impuestos licitación/lote",
                width="medium"
            ),
            "%baja": st.column_config.TextColumn(
                "%baja",
                width="small"
            ),
            "Clasificación": st.column_config.TextColumn(
                "Clasificación",
                width="medium"
            )
        }
    )
    
    # Cerrar la caja
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Mostrar información adicional sobre los links
    if 'Link licitación' in df_filtrado.columns:
        st.info("💡 **Nota:** Los links completos se muestran en la primera columna. Puedes copiar la URL para acceder a la información detallada.")
        
        # Mostrar algunos enlaces de ejemplo clickeables
        if len(df_filtrado) > 0:
            st.subheader("🔗 Enlaces clickeables (primeras 10 licitaciones)")
            
            # Obtener los datos originales con los links
            df_links_ejemplo = df_mostrar[['Link licitación', 'Aeropuerto', 'Número de expediente', 'Objeto del Contrato']].head(10)
            df_links_ejemplo = df_links_ejemplo[df_links_ejemplo['Link licitación'].notna()]
            
            # Crear columnas para mostrar los enlaces
            cols = st.columns(2)
            for idx, row in df_links_ejemplo.iterrows():
                if pd.notna(row['Link licitación']) and str(row['Link licitación']).strip() != '':
                    col_idx = idx % 2
                    with cols[col_idx]:
                        st.markdown(f"**{row['Aeropuerto']} - {row['Número de expediente']}**")
                        st.markdown(f"[🔗 Abrir licitación]({row['Link licitación']})")
                        st.markdown(f"*{row['Objeto del Contrato'][:50]}...*")
                        st.markdown("---")
    
    # Botón de descarga
    csv = df_filtrado.to_csv(index=False)
    st.download_button(
        label="📥 Descargar datos filtrados como CSV",
        data=csv,
        file_name=f"licitaciones_aena_filtradas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

# ===== FUNCIONES PARA ANÁLISIS TEMPORAL =====

def crear_grafico_licitaciones_tiempo(df):
    """Crear gráfico de licitaciones a lo largo del tiempo (anual)"""
    df_temp = df.copy()
    df_temp['Año'] = df_temp['Fecha_Publicacion'].dt.year
    df_temporal = df_temp.groupby('Año').size().reset_index(name='Licitaciones')
    df_temporal = df_temporal.sort_values('Año')
    fig = px.line(df_temporal, x='Año', y='Licitaciones', title="Licitaciones a lo largo del tiempo (Anual)", markers=True)
    fig.update_layout(height=400, xaxis_title="Año", yaxis_title="Número de Licitaciones")
    return fig

def crear_grafico_presupuesto_tiempo(df):
    """Crear gráfico de presupuesto base e importe adjudicado a lo largo del tiempo (anual)"""
    df_temp = df.copy()
    df_temp['Año'] = df_temp['Fecha_Publicacion'].dt.year
    df_temporal = df_temp.groupby('Año').agg({'Presupuesto_Base': 'sum', 'Importe_Adjudicado': 'sum'}).reset_index()
    df_temporal = df_temporal.sort_values('Año')
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_temporal['Año'], y=df_temporal['Presupuesto_Base'] / 1e6, mode='lines+markers', name='Presupuesto Base', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df_temporal['Año'], y=df_temporal['Importe_Adjudicado'] / 1e6, mode='lines+markers', name='Importe Adjudicado', line=dict(color='red')))
    fig.update_layout(title="Presupuesto Base e Importe Adjudicado a lo largo del tiempo (Anual)", xaxis_title="Año", yaxis_title="Importe (M€)", height=400)
    return fig

def crear_grafico_licitaciones_mes(df):
    """Crear gráfico de número total de adjudicaciones por mes"""
    df_mensual = df.groupby('Mes').size().reset_index(name='Licitaciones')
    fig = px.bar(df_mensual, x='Mes', y='Licitaciones', title="Número total de adjudicaciones por mes", color='Licitaciones', color_continuous_scale='Blues')
    fig.update_layout(height=400, xaxis_title="Mes", yaxis_title="Número de Licitaciones")
    return fig

# ===== FUNCIONES PARA ANÁLISIS POR AEROPUERTO =====

def crear_grafico_aeropuerto_licitaciones(df):
    """Top 10 Aeropuertos por número de licitaciones"""
    licitaciones_aeropuerto = df['Aeropuerto'].value_counts().head(10)
    fig = px.bar(x=licitaciones_aeropuerto.values, y=licitaciones_aeropuerto.index, orientation='h', title="Top 10 Aeropuertos por Número de Licitaciones", labels={'x': 'Número de Licitaciones', 'y': 'Aeropuerto'}, color=licitaciones_aeropuerto.values, color_continuous_scale='Blues')
    fig.update_layout(height=400, showlegend=False, yaxis={'categoryorder': 'total ascending'})
    return fig

def crear_grafico_aeropuerto_baja(df):
    """Top 10 Aeropuertos por porcentaje de baja (horizontal)"""
    baja_aeropuerto = df.groupby('Aeropuerto')['Porcentaje_Baja'].mean().sort_values(ascending=False).head(10)
    fig = px.bar(x=baja_aeropuerto.values, y=baja_aeropuerto.index, orientation='h', title="Top 10 Aeropuertos por Porcentaje de Baja", labels={'x': 'Porcentaje de Baja (%)', 'y': 'Aeropuerto'}, color=baja_aeropuerto.values, color_continuous_scale='Reds')
    fig.update_layout(height=400, showlegend=False, yaxis={'categoryorder': 'total ascending'})
    return fig

def crear_grafico_aeropuerto_presupuesto(df):
    """Top 10 Aeropuertos por presupuesto base"""
    presupuesto_aeropuerto = df.groupby('Aeropuerto')['Presupuesto_Base'].sum().sort_values(ascending=False).head(10)
    fig = px.bar(x=presupuesto_aeropuerto.values / 1e6, y=presupuesto_aeropuerto.index, orientation='h', title="Top 10 Aeropuertos por Presupuesto Base", labels={'x': 'Presupuesto Base (M€)', 'y': 'Aeropuerto'}, color=presupuesto_aeropuerto.values, color_continuous_scale='Greens')
    fig.update_layout(height=400, showlegend=False, yaxis={'categoryorder': 'total ascending'})
    return fig

def crear_grafico_aeropuerto_adjudicacion(df):
    """Top 10 Aeropuertos por importe adjudicado"""
    adjudicacion_aeropuerto = df.groupby('Aeropuerto')['Importe_Adjudicado'].sum().sort_values(ascending=False).head(10)
    fig = px.bar(x=adjudicacion_aeropuerto.values / 1e6, y=adjudicacion_aeropuerto.index, orientation='h', title="Top 10 Aeropuertos por Importe Adjudicado", labels={'x': 'Importe Adjudicado (M€)', 'y': 'Aeropuerto'}, color=adjudicacion_aeropuerto.values, color_continuous_scale='Purples')
    fig.update_layout(height=400, showlegend=False, yaxis={'categoryorder': 'total ascending'})
    return fig

def crear_grafico_aeropuerto_tipo_obra(df):
    """Gráfico de aeropuertos con distribución por tipo de obra"""
    df_agrupado = df.groupby(['Aeropuerto', 'Tipo_Obra']).size().reset_index(name='Licitaciones')
    df_agrupado = df_agrupado.sort_values('Licitaciones', ascending=False)
    top_aeropuertos = df['Aeropuerto'].value_counts().head(10).index
    df_agrupado = df_agrupado[df_agrupado['Aeropuerto'].isin(top_aeropuertos)]
    fig = px.bar(df_agrupado, x='Licitaciones', y='Aeropuerto', color='Tipo_Obra', orientation='h', title="Distribución de Licitaciones por Aeropuerto y Tipo de Obra", labels={'x': 'Número de Licitaciones', 'y': 'Aeropuerto'})
    fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
    return fig

# ===== FUNCIONES PARA ANÁLISIS POR TIPO DE OBRA =====

def crear_grafico_tipo_obra_licitaciones(df):
    """Tipo de obra VS número de licitaciones"""
    licitaciones_tipo = df['Tipo_Obra'].value_counts()
    fig = px.bar(x=licitaciones_tipo.values, y=licitaciones_tipo.index, orientation='h', title="Tipo de Obra VS Número de Licitaciones", labels={'x': 'Número de Licitaciones', 'y': 'Tipo de Obra'}, color=licitaciones_tipo.values, color_continuous_scale='Blues')
    fig.update_layout(height=400, showlegend=False, yaxis={'categoryorder': 'total ascending'})
    return fig

def crear_grafico_tipo_obra_presupuesto(df):
    """Tipo de obra VS presupuesto total"""
    presupuesto_tipo = df.groupby('Tipo_Obra')['Presupuesto_Base'].sum().sort_values(ascending=False)
    fig = px.bar(x=presupuesto_tipo.values / 1e6, y=presupuesto_tipo.index, orientation='h', title="Tipo de Obra VS Presupuesto Total", labels={'x': 'Presupuesto Total (M€)', 'y': 'Tipo de Obra'}, color=presupuesto_tipo.values, color_continuous_scale='Greens')
    fig.update_layout(height=400, showlegend=False, yaxis={'categoryorder': 'total ascending'})
    return fig

def crear_grafico_tipo_obra_importe(df):
    """Tipo de obra VS importe total"""
    importe_tipo = df.groupby('Tipo_Obra')['Importe_Adjudicado'].sum().sort_values(ascending=False)
    fig = px.bar(x=importe_tipo.values / 1e6, y=importe_tipo.index, orientation='h', title="Tipo de Obra VS Importe Total", labels={'x': 'Importe Total (M€)', 'y': 'Tipo de Obra'}, color=importe_tipo.values, color_continuous_scale='Purples')
    fig.update_layout(height=400, showlegend=False, yaxis={'categoryorder': 'total ascending'})
    return fig

def crear_grafico_tipo_obra_baja(df):
    """Tipo de obra VS baja promedio"""
    baja_tipo = df.groupby('Tipo_Obra')['Porcentaje_Baja'].mean().sort_values(ascending=False)
    fig = px.bar(x=baja_tipo.values, y=baja_tipo.index, orientation='h', title="Tipo de Obra VS Baja Promedio", labels={'x': 'Baja Promedio (%)', 'y': 'Tipo de Obra'}, color=baja_tipo.values, color_continuous_scale='Reds')
    fig.update_layout(height=400, showlegend=False, yaxis={'categoryorder': 'total ascending'})
    return fig

def crear_grafico_tipo_obra_tiempo(df):
    """Tipo de obra VS tiempo (evolución mensual)"""
    df_mensual_tipo = df.groupby(['Mes', 'Tipo_Obra']).size().reset_index(name='Licitaciones')
    fig = px.bar(df_mensual_tipo, x='Mes', y='Licitaciones', color='Tipo_Obra', title="Evolución Mensual por Tipo de Obra", labels={'x': 'Mes', 'y': 'Número de Licitaciones'})
    fig.update_layout(height=400, xaxis_title="Mes", yaxis_title="Número de Licitaciones")
    return fig

def crear_grafico_tipo_obra_aeropuertos(df):
    """Tipo de obra VS aeropuertos (distribución)"""
    df_aeropuerto_tipo = df.groupby(['Tipo_Obra', 'Aeropuerto']).size().reset_index(name='Licitaciones')
    top_aeropuertos = df['Aeropuerto'].value_counts().head(10).index
    df_aeropuerto_tipo = df_aeropuerto_tipo[df_aeropuerto_tipo['Aeropuerto'].isin(top_aeropuertos)]
    fig = px.bar(df_aeropuerto_tipo, x='Licitaciones', y='Tipo_Obra', color='Aeropuerto', orientation='h', title="Distribución de Tipos de Obra por Aeropuerto", labels={'x': 'Número de Licitaciones', 'y': 'Tipo de Obra'})
    fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
    return fig

# ===== FUNCIONES PARA ANÁLISIS POR EMPRESA =====

def crear_grafico_empresa_licitaciones(df):
    """Top 10 empresas VS número de licitaciones"""
    licitaciones_empresa = df['Empresa_Adjudicataria'].value_counts().head(10)
    fig = px.bar(x=licitaciones_empresa.values, y=licitaciones_empresa.index, orientation='h', title="Top 10 Empresas VS Número de Licitaciones", labels={'x': 'Número de Licitaciones', 'y': 'Empresa'}, color=licitaciones_empresa.values, color_continuous_scale='Blues')
    fig.update_layout(height=400, showlegend=False, yaxis={'categoryorder': 'total ascending'})
    return fig

def crear_grafico_empresa_presupuesto(df):
    """Top 10 empresas VS presupuesto total"""
    presupuesto_empresa = df.groupby('Empresa_Adjudicataria')['Presupuesto_Base'].sum().sort_values(ascending=False).head(10)
    fig = px.bar(x=presupuesto_empresa.values / 1e6, y=presupuesto_empresa.index, orientation='h', title="Top 10 Empresas VS Presupuesto Total", labels={'x': 'Presupuesto Total (M€)', 'y': 'Empresa'}, color=presupuesto_empresa.values, color_continuous_scale='Greens')
    fig.update_layout(height=400, showlegend=False, yaxis={'categoryorder': 'total ascending'})
    return fig

def crear_grafico_empresa_importe(df):
    """Top 10 empresas VS importe total"""
    importe_empresa = df.groupby('Empresa_Adjudicataria')['Importe_Adjudicado'].sum().sort_values(ascending=False).head(10)
    fig = px.bar(x=importe_empresa.values / 1e6, y=importe_empresa.index, orientation='h', title="Top 10 Empresas VS Importe Total", labels={'x': 'Importe Total (M€)', 'y': 'Empresa'}, color=importe_empresa.values, color_continuous_scale='Purples')
    fig.update_layout(height=400, showlegend=False, yaxis={'categoryorder': 'total ascending'})
    return fig

def crear_grafico_empresa_baja(df):
    """Top 10 empresas VS baja promedio"""
    baja_empresa = df.groupby('Empresa_Adjudicataria')['Porcentaje_Baja'].mean().sort_values(ascending=False).head(10)
    fig = px.bar(x=baja_empresa.values, y=baja_empresa.index, orientation='h', title="Top 10 Empresas VS Baja Promedio", labels={'x': 'Baja Promedio (%)', 'y': 'Empresa'}, color=baja_empresa.values, color_continuous_scale='Reds')
    fig.update_layout(height=400, showlegend=False, yaxis={'categoryorder': 'total ascending'})
    return fig

def mostrar_empresas_por_aeropuerto(df):
    """Mostrar listado de empresas con más contratos en cada aeropuerto"""
    st.subheader("🏢 Empresa Líder por Aeropuerto")
    empresa_lider = df.groupby('Aeropuerto')['Empresa_Adjudicataria'].apply(lambda x: x.value_counts().index[0]).reset_index()
    empresa_lider.columns = ['Aeropuerto', 'Empresa_Lider']
    contratos_lider = df.groupby(['Aeropuerto', 'Empresa_Adjudicataria']).size().reset_index(name='Contratos')
    contratos_lider = contratos_lider.loc[contratos_lider.groupby('Aeropuerto')['Contratos'].idxmax()]
    resultado = empresa_lider.merge(contratos_lider[['Aeropuerto', 'Contratos']], on='Aeropuerto')
    resultado = resultado.sort_values('Contratos', ascending=False)
    st.dataframe(resultado, use_container_width=True)

# ===== FUNCIONES PARA ANÁLISIS POR BAJA =====

def crear_grafico_baja_aeropuertos(df):
    """Baja VS Aeropuertos (vertical)"""
    baja_aeropuerto = df.groupby('Aeropuerto')['Porcentaje_Baja'].mean().sort_values(ascending=False)
    fig = px.bar(x=baja_aeropuerto.index, y=baja_aeropuerto.values, title="Porcentaje de Baja por Aeropuerto", labels={'x': 'Aeropuerto', 'y': 'Porcentaje de Baja (%)'}, color=baja_aeropuerto.values, color_continuous_scale='Reds')
    fig.update_layout(height=600, showlegend=False, xaxis_tickangle=-45)
    return fig

def crear_grafico_baja_rangos_importe(df):
    """Baja en función del importe total (Rangos)"""
    df['Rango_Importe'] = pd.cut(df['Importe_Adjudicado'], bins=[0, 10000, 50000, 100000, 500000, 1000000, float('inf')], labels=['<10K€', '10K-50K€', '50K-100K€', '100K-500K€', '500K-1M€', '>1M€'])
    baja_rango = df.groupby('Rango_Importe')['Porcentaje_Baja'].mean().dropna()
    fig = px.bar(x=baja_rango.index, y=baja_rango.values, title="Porcentaje de Baja por Rango de Importe", labels={'x': 'Rango de Importe', 'y': 'Porcentaje de Baja (%)'}, color=baja_rango.values, color_continuous_scale='Reds')
    fig.update_layout(height=400, showlegend=False)
    return fig

# ===== FUNCIONES DE MÉTRICAS Y FILTROS =====

def mostrar_metricas_principales(df):
    """Mostrar métricas principales del dashboard"""
    st.markdown("### 📊 Datos Generales")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Total Licitaciones", f"{len(df):,}")
    
    with col2:
        presupuesto_total = df['Presupuesto_Base'].sum() / 1e6
        st.metric("Presupuesto Total", f"{presupuesto_total:.1f} M€")
    
    with col3:
        importe_total = df['Importe_Adjudicado'].sum() / 1e6
        st.metric("Importe Adjudicado", f"{importe_total:.1f} M€")
    
    with col4:
        ahorro_total = (df['Presupuesto_Base'].sum() - df['Importe_Adjudicado'].sum()) / 1e6
        st.metric("Ahorro Total", f"{ahorro_total:.1f} M€")
    
    with col5:
        baja_media = df['Porcentaje_Baja'].mean()
        st.metric("% Baja Media", f"{baja_media:.1f}%")
    
    with col6:
        # Baja ponderada en función del presupuesto
        total_presupuesto = df['Presupuesto_Base'].sum()
        baja_ponderada = (df['Porcentaje_Baja'] * df['Presupuesto_Base']).sum() / total_presupuesto
        st.metric("% Baja Ponderada", f"{baja_ponderada:.1f}%")

def mostrar_filtros_sidebar(df):
    """Mostrar filtros en el sidebar"""
    st.sidebar.header("🔍 Filtros")
    
    # Filtro por aeropuerto
    aeropuertos = ['Todos'] + sorted(df['Aeropuerto'].unique().tolist())
    aeropuerto_seleccionado = st.sidebar.selectbox("Aeropuerto", aeropuertos)
    
    # Filtro por tipo de obra
    tipos_obra = ['Todos'] + sorted(df['Tipo_Obra'].unique().tolist())
    tipo_obra_seleccionado = st.sidebar.selectbox("Tipo de Obra", tipos_obra)
    
    # Filtro por empresa
    empresas = ['Todas'] + sorted(df['Empresa_Adjudicataria'].unique().tolist())
    empresa_seleccionada = st.sidebar.selectbox("Empresa Adjudicataria", empresas)
    
    # Filtro por rango de presupuesto
    st.sidebar.subheader("Rango de Presupuesto (€)")
    presupuesto_min = st.sidebar.number_input("Presupuesto Mínimo", min_value=0.0, value=0.0, step=1000.0)
    presupuesto_max = st.sidebar.number_input("Presupuesto Máximo", min_value=0.0, value=float(df['Presupuesto_Base'].max()), step=1000.0)
    
    # Filtro por rango de baja
    st.sidebar.subheader("Rango de Baja (%)")
    baja_min = st.sidebar.number_input("Baja Mínima", min_value=0.0, value=0.0, step=0.1)
    baja_max = st.sidebar.number_input("Baja Máxima", min_value=0.0, value=100.0, step=0.1)
    
    return {
        'aeropuerto': aeropuerto_seleccionado,
        'tipo_obra': tipo_obra_seleccionado,
        'empresa': empresa_seleccionada,
        'presupuesto_min': presupuesto_min,
        'presupuesto_max': presupuesto_max,
        'baja_min': baja_min,
        'baja_max': baja_max
    }

def aplicar_filtros(df, filtros):
    """Aplicar filtros al DataFrame"""
    df_filtrado = df.copy()
    
    # Filtro por aeropuerto
    if filtros['aeropuerto'] != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Aeropuerto'] == filtros['aeropuerto']]
    
    # Filtro por tipo de obra
    if filtros['tipo_obra'] != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Tipo_Obra'] == filtros['tipo_obra']]
    
    # Filtro por empresa
    if filtros['empresa'] != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Empresa_Adjudicataria'] == filtros['empresa']]
    
    # Filtro por rango de baja
    df_filtrado = df_filtrado[
        (df_filtrado['Porcentaje_Baja'] >= filtros['baja_min']) &
        (df_filtrado['Porcentaje_Baja'] <= filtros['baja_max'])
    ]
    
    # Filtro por rango de presupuesto
    df_filtrado = df_filtrado[
        (df_filtrado['Presupuesto_Base'] >= filtros['presupuesto_min']) &
        (df_filtrado['Presupuesto_Base'] <= filtros['presupuesto_max'])
    ]
    
    return df_filtrado

def main():
    """Función principal del dashboard"""
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>✈️ Dashboard de Licitaciones AENA</h1>
        <p>Análisis integral de licitaciones y contrataciones</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Cargar datos
    df = cargar_datos()
    if df is None or len(df) == 0:
        st.warning("⚠️ No se pudieron cargar los datos del archivo Excel.")
        return
    else:
        st.success(f"✅ Datos cargados correctamente: {len(df)} licitaciones de AENA 2024")
    
    # Mostrar filtros en sidebar
    filtros = mostrar_filtros_sidebar(df)
    
    # Aplicar filtros
    df_filtrado = aplicar_filtros(df, filtros)
    
    # Mostrar métricas principales
    mostrar_metricas_principales(df_filtrado)
    
    # Crear pestañas
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📅 Análisis Temporal", 
        "🏢 Por Aeropuerto", 
        "🔧 Por Tipo de Obra", 
        "🏭 Por Empresa", 
        "📉 Por Baja",
        "📊 Datos",
        "🤖 IA"
    ])
    
    with tab1:
        st.subheader("📅 Análisis Temporal")
        
        # Gráfico de licitaciones a lo largo del tiempo (anual)
        fig_licitaciones_tiempo = crear_grafico_licitaciones_tiempo(df_filtrado)
        st.plotly_chart(fig_licitaciones_tiempo, use_container_width=True)
        
        # Gráfico de presupuesto base e importe adjudicado a lo largo del tiempo (anual)
        fig_presupuesto_tiempo = crear_grafico_presupuesto_tiempo(df_filtrado)
        st.plotly_chart(fig_presupuesto_tiempo, use_container_width=True)
        
        # Gráfico de licitaciones por mes
        fig_licitaciones_mes = crear_grafico_licitaciones_mes(df_filtrado)
        st.plotly_chart(fig_licitaciones_mes, use_container_width=True)
    
    with tab2:
        st.subheader("🏢 Análisis por Aeropuerto")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_aeropuerto_licitaciones = crear_grafico_aeropuerto_licitaciones(df_filtrado)
            st.plotly_chart(fig_aeropuerto_licitaciones, use_container_width=True)
        
        with col2:
            fig_aeropuerto_baja = crear_grafico_aeropuerto_baja(df_filtrado)
            st.plotly_chart(fig_aeropuerto_baja, use_container_width=True)
        
        col3, col4 = st.columns(2)
        
        with col3:
            fig_aeropuerto_presupuesto = crear_grafico_aeropuerto_presupuesto(df_filtrado)
            st.plotly_chart(fig_aeropuerto_presupuesto, use_container_width=True)
        
        with col4:
            fig_aeropuerto_adjudicacion = crear_grafico_aeropuerto_adjudicacion(df_filtrado)
            st.plotly_chart(fig_aeropuerto_adjudicacion, use_container_width=True)
        
        # Gráfico de distribución por tipo de obra
        fig_aeropuerto_tipo_obra = crear_grafico_aeropuerto_tipo_obra(df_filtrado)
        st.plotly_chart(fig_aeropuerto_tipo_obra, use_container_width=True)
    
    with tab3:
        st.subheader("🔧 Análisis por Tipo de Obra")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_tipo_obra_licitaciones = crear_grafico_tipo_obra_licitaciones(df_filtrado)
            st.plotly_chart(fig_tipo_obra_licitaciones, use_container_width=True)
        
        with col2:
            fig_tipo_obra_presupuesto = crear_grafico_tipo_obra_presupuesto(df_filtrado)
            st.plotly_chart(fig_tipo_obra_presupuesto, use_container_width=True)
        
        col3, col4 = st.columns(2)
        
        with col3:
            fig_tipo_obra_importe = crear_grafico_tipo_obra_importe(df_filtrado)
            st.plotly_chart(fig_tipo_obra_importe, use_container_width=True)
        
        with col4:
            fig_tipo_obra_baja = crear_grafico_tipo_obra_baja(df_filtrado)
            st.plotly_chart(fig_tipo_obra_baja, use_container_width=True)
        
        # Gráfico de evolución mensual por tipo de obra (ancho completo)
        fig_tipo_obra_tiempo = crear_grafico_tipo_obra_tiempo(df_filtrado)
        st.plotly_chart(fig_tipo_obra_tiempo, use_container_width=True)
        
        # Gráfico de distribución de tipos de obra por aeropuerto (ancho completo)
        fig_tipo_obra_aeropuertos = crear_grafico_tipo_obra_aeropuertos(df_filtrado)
        st.plotly_chart(fig_tipo_obra_aeropuertos, use_container_width=True)
    
    with tab4:
        st.subheader("🏭 Análisis por Empresa")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_empresa_licitaciones = crear_grafico_empresa_licitaciones(df_filtrado)
            st.plotly_chart(fig_empresa_licitaciones, use_container_width=True)
        
        with col2:
            fig_empresa_presupuesto = crear_grafico_empresa_presupuesto(df_filtrado)
            st.plotly_chart(fig_empresa_presupuesto, use_container_width=True)
        
        col3, col4 = st.columns(2)
        
        with col3:
            fig_empresa_importe = crear_grafico_empresa_importe(df_filtrado)
            st.plotly_chart(fig_empresa_importe, use_container_width=True)
        
        with col4:
            fig_empresa_baja = crear_grafico_empresa_baja(df_filtrado)
            st.plotly_chart(fig_empresa_baja, use_container_width=True)
        
        # Listado de empresas líderes por aeropuerto
        mostrar_empresas_por_aeropuerto(df_filtrado)
    
    with tab5:
        st.subheader("📉 Análisis por Baja")
        
        # Gráfico de porcentaje de baja por aeropuerto (vertical)
        fig_baja_aeropuertos = crear_grafico_baja_aeropuertos(df_filtrado)
        st.plotly_chart(fig_baja_aeropuertos, use_container_width=True)
        
        # Gráfico de baja por rangos de importe
        fig_baja_rangos = crear_grafico_baja_rangos_importe(df_filtrado)
        st.plotly_chart(fig_baja_rangos, use_container_width=True)
    
    with tab6:
        mostrar_tabla_detallada(df_filtrado)
    
    with tab7:
        st.subheader("🤖 IA")
        
        # Botón para GPT Competenc-IA
        if st.button("GPT Competenc-IA", type="primary"):
            st.markdown(f'<meta http-equiv="refresh" content="0; url=https://chatgpt.com/g/g-68db911ff44481919538e7bc1da992ff-competenc-ia">', unsafe_allow_html=True)
            st.markdown('<script>window.open("https://chatgpt.com/g/g-68db911ff44481919538e7bc1da992ff-competenc-ia", "_blank");</script>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
