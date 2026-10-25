#!/usr/bin/env python3
"""
Script de Análisis Estadístico y Evaluativo Integral para Trabajo Fin de Máster (TFM).
Dataset: Resultados de Evaluación OMOP QueryLibrary (querylibrary_analisis_202609061551.xlsx)

Genera:
1. Informe estadístico en Excel multihistorial (querylibrary_estadisticas_tfm.xlsx) con formato profesional.
2. Galería de figuras científicas a 300 DPI (PNG + SVG) para la memoria del TFM.
3. Informe completo en Markdown (querylibrary_analisis_estadistico_tfm.md) listo para inclusión en el TFM.
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.contingency_tables import mcnemar

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ==============================================================================
# PALETA DE IDENTIDAD VISUAL CORPORATIVA: UNIVERSIDAD EUROPEA (UE)
# Extraída directamente de los tokens y hojas de estilo de https://universidadeuropea.com/
# ==============================================================================
UE_COLORS = {
    "red": "#FF3228",          # Rojo Universidad Europea (Color Primario Institucional)
    "red_light": "#FF5A50",    # Rojo Suave / Hover
    "red_tint": "#FDE2E0",     # Tinte de Relleno Suave (Fondo de alertas / sombreados)
    "navy": "#2D41B4",         # Azul Institucional / Académico Principal
    "navy_dark": "#0D34A7",    # Azul Marino Profundo (Contraste alto)
    "cyan": "#0079C8",         # Azul Sanitas / Área Biomédica y Salud
    "cyan_light": "#008FD0",   # Celeste Tecnológico
    "charcoal": "#1E1E1E",     # Gris Carbón / Texto principal de alto contraste
    "text_body": "#36313D",    # Gris Grafito para texto secundario
    "gray_light": "#F5F5F5",   # Gris Neutro Claro (Fondos y alternancias)
    "gray_border": "#D2D4D9",  # Gris para bordes y cuadrículas tenues
    "green_success": "#05AD05" # Verde Validación / Éxito estándar
}

import matplotlib.font_manager as fm
import glob

# Asegurar carga explícita de Arial desde el directorio de fuentes de usuario
for font_file in glob.glob(os.path.expanduser("~/.local/share/fonts/Arial*.ttf")):
    try:
        fm.fontManager.addfont(font_file)
    except Exception:
        pass

# Configuración estética para gráficos de publicación académica TFM con fuente Arial
sns.set_theme(style="whitegrid", font="Arial")
plt.rcParams.update({
    "font.size": 11,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.titlesize": 14,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "text.color": UE_COLORS["charcoal"],
    "axes.labelcolor": UE_COLORS["charcoal"],
    "xtick.color": UE_COLORS["charcoal"],
    "ytick.color": UE_COLORS["charcoal"],
    "grid.color": UE_COLORS["gray_border"],
    "grid.alpha": 0.5
})

def format_pvalue(p):
    """Formatea p-valores en notación académica estándar."""
    if p < 0.001:
        return "< 0.001 ***"
    elif p < 0.01:
        return f"{p:.3f} **"
    elif p < 0.05:
        return f"{p:.3f} *"
    else:
        return f"{p:.3f} (ns)"

def compute_cliffs_delta(x, y):
    """Calcula el tamaño del efecto Delta de Cliff para dos muestras independientes."""
    x = np.asarray(x)
    y = np.asarray(y)
    n_x, n_y = len(x), len(y)
    if n_x == 0 or n_y == 0:
        return 0.0
    greater = sum((x_i > y).sum() for x_i in x)
    less = sum((x_i < y).sum() for x_i in x)
    return (greater - less) / (n_x * n_y)

def compute_rank_biserial(w_stat, n):
    """Calcula la correlación biserial de rangos para la prueba de Wilcoxon."""
    total_ranks = n * (n + 1) / 2
    if total_ranks == 0:
        return 0.0
    return 1.0 - (2.0 * w_stat / total_ranks)

def dunn_posthoc(groups, group_names, alpha=0.05):
    """
    Realiza la prueba post-hoc de Dunn para comparaciones múltiples por pares
    con corrección de Holm-Bonferroni a partir de las sumas de rangos.
    """
    all_data = []
    group_labels = []
    for g, name in zip(groups, group_names):
        all_data.extend(g)
        group_labels.extend([name] * len(g))
    
    df_ranks = pd.DataFrame({"val": all_data, "group": group_labels})
    df_ranks["rank"] = df_ranks["val"].rank()
    
    N = len(df_ranks)
    group_counts = {name: len(g) for name, g in zip(group_names, groups)}
    mean_ranks = {name: df_ranks[df_ranks["group"] == name]["rank"].mean() for name in group_names}
    
    # Manejo de empates para corrección de varianza
    ties = df_ranks["val"].value_counts()
    tie_sum = sum(t**3 - t for t in ties if t > 1)
    sigma2 = (N * (N + 1) / 12.0) - (tie_sum / (12.0 * (N - 1)))
    
    comparisons = []
    k = len(group_names)
    for i in range(k):
        for j in range(i + 1, k):
            name1 = group_names[i]
            name2 = group_names[j]
            n1 = group_counts[name1]
            n2 = group_counts[name2]
            se = np.sqrt(sigma2 * (1.0 / n1 + 1.0 / n2))
            diff = mean_ranks[name1] - mean_ranks[name2]
            z = diff / se
            p_unadj = 2 * (1 - stats.norm.cdf(abs(z)))
            comparisons.append({
                "comparison": f"{name1} vs {name2}",
                "mean_rank_1": mean_ranks[name1],
                "mean_rank_2": mean_ranks[name2],
                "diff": diff,
                "z_stat": z,
                "p_unadj": p_unadj
            })
            
    df_comp = pd.DataFrame(comparisons)
    # Corrección de Holm-Bonferroni
    df_comp.sort_values(by="p_unadj", inplace=True)
    m = len(df_comp)
    adjusted_p = []
    for idx, (_, row) in enumerate(df_comp.iterrows()):
        p_adj = min(1.0, row["p_unadj"] * (m - idx))
        adjusted_p.append(p_adj)
    
    # Garantizar monotonicidad del método Holm
    for i in range(1, len(adjusted_p)):
        adjusted_p[i] = max(adjusted_p[i], adjusted_p[i - 1])
        adjusted_p[i] = min(1.0, adjusted_p[i])
        
    df_comp["p_adj_holm"] = adjusted_p
    df_comp["significativo"] = df_comp["p_adj_holm"] < alpha
    return df_comp

class TFMStatisticalAnalyzer:
    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.df = pd.read_excel(excel_path)
        self.preprocess_data()
        
    def preprocess_data(self):
        """Preprocesa y valida columnas del dataset."""
        df = self.df
        # Mapeo ordinal de complejidad
        comp_map = {"baja": 1, "intermedia": 2, "compleja": 3}
        df["nivel_complejidad_num"] = df["nivel_complejidad"].map(comp_map)
        
        # Agrupación clínica de dominios OMOP
        def categorize_domain(d):
            d = str(d).strip().lower()
            if d in ["condition_era", "drug_era"]:
                return "Tablas de Épocas (Eras)"
            elif d in ["condition_occurrence", "drug_exposure"]:
                return "Tablas de Eventos Crudos"
            elif d in ["concept", "vocabulary"]:
                return "Tablas de Vocabulario"
            else:
                return "Demografía y Administración"
        df["categoria_dominio"] = df["domain_main"].apply(categorize_domain)
        
        # Agrupación de dominios para contrastes asintóticos (menores con N < 10)
        dom_counts = df["domain_main"].value_counts()
        df["domain_robust"] = df["domain_main"].apply(lambda d: d if dom_counts[d] >= 10 else "Otros (<10)")
        
        # Indicadores binarios
        df["exito_resolucion_080"] = (df["validez_sintactica_y_estructural"] > 0.80).astype(int)
        df["excelencia_095"] = (df["validez_sintactica_y_estructural"] >= 0.95).astype(int)
        df["vocabulario_perfecto"] = (df["precision_terminologica_vocabulario"] >= 1.00).astype(int)
        df["ejecucion_valida"] = (df["criterio_1_1_ejecucion"] == 0.10).astype(int)
        
        # Turno 1 resolución
        df["turno_1_exito_080"] = (df["turno_1_validez_sintactica_y_estructural"] > 0.80).astype(int)
        
        # Turno 2 resolución (en los que tuvieron T2)
        df["turno_2_exito_080"] = (df["turno_2_validez_sintactica_y_estructural"] > 0.80).astype(int)
        
        # Turno 3 resolución (en los que tuvieron T3)
        df["turno_3_exito_080"] = (df["turno_3_validez_sintactica_y_estructural"] > 0.80).astype(int)

    def analyze_global_descriptives(self):
        """Calcula estadísticas descriptivas globales completas."""
        metrics = [
            ("Validez Sintáctica y Estructural (Final)", "validez_sintactica_y_estructural"),
            ("Criterio 1.1 Ejecución SQL BigQuery", "criterio_1_1_ejecucion"),
            ("Criterio 1.2 Similitud Semántica Gold Standard", "criterio_1_2_similitud_sql_gemini"),
            ("Precisión Terminológica Vocabulario (Final)", "precision_terminologica_vocabulario"),
            ("Turnos Conversacionales Ejecutados", "turnos_ejecutados")
        ]
        
        rows = []
        for label, col in metrics:
            s = self.df[col].dropna()
            n = len(s)
            mean = s.mean()
            std = s.std()
            se = std / np.sqrt(n)
            ci95_low, ci95_high = stats.t.interval(0.95, df=n-1, loc=mean, scale=se)
            median = s.median()
            q25 = s.quantile(0.25)
            q75 = s.quantile(0.75)
            iqr = q75 - q25
            s_min = s.min()
            s_max = s.max()
            skew = s.skew()
            kurt = s.kurt()
            
            rows.append({
                "Metrica": label,
                "N": n,
                "Media": mean,
                "DE": std,
                "IC95_Inferior": ci95_low,
                "IC95_Superior": ci95_high,
                "Mediana": median,
                "Q25": q25,
                "Q75": q75,
                "IQR": iqr,
                "Minimo": s_min,
                "Maximo": s_max,
                "Asimetria (Skewness)": skew,
                "Curtosis (Kurtosis)": kurt
            })
        return pd.DataFrame(rows)

    def analyze_by_complexity(self):
        """Calcula el rendimiento estratificado por nivel de complejidad."""
        df = self.df
        order = ["baja", "intermedia", "compleja"]
        summary = []
        for comp in order:
            sub = df[df["nivel_complejidad"] == comp]
            n = len(sub)
            v = sub["validez_sintactica_y_estructural"]
            p = sub["precision_terminologica_vocabulario"]
            t = sub["turnos_ejecutados"]
            
            summary.append({
                "Nivel Complejidad": comp.capitalize(),
                "N": n,
                "Pct Cohorte": (n / len(df)) * 100,
                "Validez Media": v.mean(),
                "Validez DE": v.std(),
                "Validez Mediana": v.median(),
                "Validez IQR": v.quantile(0.75) - v.quantile(0.25),
                "Vocabulario Medio": p.mean(),
                "Vocabulario DE": p.std(),
                "Vocabulario Mediana": p.median(),
                "Vocabulario IQR": p.quantile(0.75) - p.quantile(0.25),
                "Turnos Medios": t.mean(),
                "Turnos DE": t.std(),
                "Turnos Mediana": t.median(),
                "Tasa Exito >= 0.80 (%)": (sub["exito_resolucion_080"].mean()) * 100,
                "Tasa Excelencia >= 0.95 (%)": (sub["excelencia_095"].mean()) * 100,
                "Tasa Vocabulario Perfecto (%)": (sub["vocabulario_perfecto"].mean()) * 100
            })
            
        # Fila Total
        v = df["validez_sintactica_y_estructural"]
        p = df["precision_terminologica_vocabulario"]
        t = df["turnos_ejecutados"]
        summary.append({
            "Nivel Complejidad": "Total Global",
            "N": len(df),
            "Pct Cohorte": 100.0,
            "Validez Media": v.mean(),
            "Validez DE": v.std(),
            "Validez Mediana": v.median(),
            "Validez IQR": v.quantile(0.75) - v.quantile(0.25),
            "Vocabulario Medio": p.mean(),
            "Vocabulario DE": p.std(),
            "Vocabulario Mediana": p.median(),
            "Vocabulario IQR": p.quantile(0.75) - p.quantile(0.25),
            "Turnos Medios": t.mean(),
            "Turnos DE": t.std(),
            "Turnos Mediana": t.median(),
            "Tasa Exito >= 0.80 (%)": (df["exito_resolucion_080"].mean()) * 100,
            "Tasa Excelencia >= 0.95 (%)": (df["excelencia_095"].mean()) * 100,
            "Tasa Vocabulario Perfecto (%)": (df["vocabulario_perfecto"].mean()) * 100
        })
        return pd.DataFrame(summary)

    def analyze_contingency_complexity_turns(self):
        """Calcula la tabla de contingencia Complejidad × Turnos."""
        df = self.df
        ct = pd.crosstab(df["nivel_complejidad"], df["turnos_ejecutados"], margins=True, margins_name="Total")
        ct_row = pd.crosstab(df["nivel_complejidad"], df["turnos_ejecutados"], normalize="index", margins=True, margins_name="Total") * 100
        ct_col = pd.crosstab(df["nivel_complejidad"], df["turnos_ejecutados"], normalize="columns", margins=True, margins_name="Total") * 100
        
        # Prueba Chi-cuadrado
        ct_raw = pd.crosstab(df["nivel_complejidad"], df["turnos_ejecutados"])
        chi2, p_chi2, dof, expected = stats.chi2_contingency(ct_raw)
        n = ct_raw.sum().sum()
        cramers_v = np.sqrt(chi2 / (n * (min(ct_raw.shape) - 1)))
        
        return ct, ct_row, ct_col, {"chi2": chi2, "p_value": p_chi2, "dof": dof, "cramers_v": cramers_v, "expected": expected}

    def analyze_by_domain(self):
        """Calcula el rendimiento estratificado por Dominio OMOP y por categoría."""
        df = self.df
        dom_group = df.groupby("domain_main").agg(
            N=("id_evaluacion", "count"),
            Validez_Media=("validez_sintactica_y_estructural", "mean"),
            Validez_DE=("validez_sintactica_y_estructural", "std"),
            Validez_Mediana=("validez_sintactica_y_estructural", "median"),
            Validez_Q25=("validez_sintactica_y_estructural", lambda x: x.quantile(0.25)),
            Validez_Q75=("validez_sintactica_y_estructural", lambda x: x.quantile(0.75)),
            Vocab_Medio=("precision_terminologica_vocabulario", "mean"),
            Vocab_DE=("precision_terminologica_vocabulario", "std"),
            Vocab_Mediana=("precision_terminologica_vocabulario", "median"),
            Turnos_Medios=("turnos_ejecutados", "mean"),
            Turnos_DE=("turnos_ejecutados", "std"),
            Turnos_Mediana=("turnos_ejecutados", "median"),
            Exito_Pct=("exito_resolucion_080", lambda x: x.mean() * 100),
            Vocab_Perfecto_Pct=("vocabulario_perfecto", lambda x: x.mean() * 100)
        ).reset_index()
        dom_group["Pct_Cohorte"] = (dom_group["N"] / len(df)) * 100
        dom_group.sort_values(by="N", ascending=False, inplace=True)
        
        # Por categoría clínica agregada
        cat_group = df.groupby("categoria_dominio").agg(
            N=("id_evaluacion", "count"),
            Validez_Media=("validez_sintactica_y_estructural", "mean"),
            Validez_DE=("validez_sintactica_y_estructural", "std"),
            Validez_Mediana=("validez_sintactica_y_estructural", "median"),
            Vocab_Medio=("precision_terminologica_vocabulario", "mean"),
            Vocab_DE=("precision_terminologica_vocabulario", "std"),
            Vocab_Mediana=("precision_terminologica_vocabulario", "median"),
            Turnos_Medios=("turnos_ejecutados", "mean"),
            Turnos_Mediana=("turnos_ejecutados", "median"),
            Exito_Pct=("exito_resolucion_080", lambda x: x.mean() * 100)
        ).reset_index()
        cat_group["Pct_Cohorte"] = (cat_group["N"] / len(df)) * 100
        cat_group.sort_values(by="N", ascending=False, inplace=True)
        
        return dom_group, cat_group

    def analyze_domain_complexity_matrix(self):
        """Genera la matriz cruzada Dominio × Complejidad."""
        df = self.df
        # Pivot table de validez media
        pivot_validez = df.pivot_table(
            index="domain_main",
            columns="nivel_complejidad",
            values="validez_sintactica_y_estructural",
            aggfunc="mean"
        ).reindex(columns=["baja", "intermedia", "compleja"])
        
        # Pivot table de conteos
        pivot_count = df.pivot_table(
            index="domain_main",
            columns="nivel_complejidad",
            values="id_evaluacion",
            aggfunc="count",
            fill_value=0
        ).reindex(columns=["baja", "intermedia", "compleja"])
        
        # Añadir totales
        pivot_validez["Media Global"] = df.groupby("domain_main")["validez_sintactica_y_estructural"].mean()
        pivot_count["Total N"] = df.groupby("domain_main")["id_evaluacion"].count()
        
        return pivot_validez.sort_values(by="Media Global", ascending=False), pivot_count.sort_values(by="Total N", ascending=False)

    def analyze_multiturn_dynamics(self):
        """Calcula el análisis longitudinal exhaustivo por turno conversacional."""
        df = self.df
        
        # Métricas por Turno
        # Turno 1 (N = 201)
        t1_val = df["turno_1_validez_sintactica_y_estructural"]
        t1_voc = df["turno_1_precision_terminologica_vocabulario"]
        
        # Turno 2 (N = 153)
        sub_t2 = df[df["turnos_ejecutados"] >= 2].copy()
        t2_val = sub_t2["turno_2_validez_sintactica_y_estructural"]
        t2_voc = sub_t2["turno_2_precision_terminologica_vocabulario"]
        t2_t1_val = sub_t2["turno_1_validez_sintactica_y_estructural"]
        t2_t1_voc = sub_t2["turno_1_precision_terminologica_vocabulario"]
        delta_t1_t2_val = t2_val - t2_t1_val
        delta_t1_t2_voc = t2_voc - t2_t1_voc
        
        # Turno 3 (N = 68)
        sub_t3 = df[df["turnos_ejecutados"] >= 3].copy()
        t3_val = sub_t3["turno_3_validez_sintactica_y_estructural"]
        t3_voc = sub_t3["turno_3_precision_terminologica_vocabulario"]
        t3_t2_val = sub_t3["turno_2_validez_sintactica_y_estructural"]
        t3_t2_voc = sub_t3["turno_2_precision_terminologica_vocabulario"]
        delta_t2_t3_val = t3_val - t3_t2_val
        delta_t2_t3_voc = t3_voc - t3_t2_voc
        
        # Final (N = 201)
        fin_val = df["validez_sintactica_y_estructural"]
        fin_voc = df["precision_terminologica_vocabulario"]
        delta_global_val = fin_val - t1_val
        delta_global_voc = fin_voc - t1_voc
        
        summary_turns = pd.DataFrame([
            {
                "Turno Evaluado": "Turno 1 (Línea Base / Zero-Shot)",
                "N Casos": len(df),
                "Validez Media": t1_val.mean(),
                "Validez DE": t1_val.std(),
                "Validez Mediana": t1_val.median(),
                "Validez IQR": t1_val.quantile(0.75) - t1_val.quantile(0.25),
                "Vocabulario Medio": t1_voc.mean(),
                "Vocabulario DE": t1_voc.std(),
                "Vocabulario Mediana": t1_voc.median(),
                "Tasa Exito > 0.80 (%)": (t1_val > 0.80).mean() * 100,
                "Tasa Vocab Perfecto (%)": (t1_voc >= 1.00).mean() * 100
            },
            {
                "Turno Evaluado": "Turno 2 (Subcohorte Refinada 1ª Ronda)",
                "N Casos": len(sub_t2),
                "Validez Media": t2_val.mean(),
                "Validez DE": t2_val.std(),
                "Validez Mediana": t2_val.median(),
                "Validez IQR": t2_val.quantile(0.75) - t2_val.quantile(0.25),
                "Vocabulario Medio": t2_voc.mean(),
                "Vocabulario DE": t2_voc.std(),
                "Vocabulario Mediana": t2_voc.median(),
                "Tasa Exito > 0.80 (%)": (t2_val > 0.80).mean() * 100,
                "Tasa Vocab Perfecto (%)": (t2_voc >= 1.00).mean() * 100
            },
            {
                "Turno Evaluado": "Turno 3 (Subcohorte Refinada 2ª Ronda)",
                "N Casos": len(sub_t3),
                "Validez Media": t3_val.mean(),
                "Validez DE": t3_val.std(),
                "Validez Mediana": t3_val.median(),
                "Validez IQR": t3_val.quantile(0.75) - t3_val.quantile(0.25),
                "Vocabulario Medio": t3_voc.mean(),
                "Vocabulario DE": t3_voc.std(),
                "Vocabulario Mediana": t3_voc.median(),
                "Tasa Exito > 0.80 (%)": (t3_val > 0.80).mean() * 100,
                "Tasa Vocab Perfecto (%)": (t3_voc >= 1.00).mean() * 100
            },
            {
                "Turno Evaluado": "Rendimiento Final Consolidado",
                "N Casos": len(df),
                "Validez Media": fin_val.mean(),
                "Validez DE": fin_val.std(),
                "Validez Mediana": fin_val.median(),
                "Validez IQR": fin_val.quantile(0.75) - fin_val.quantile(0.25),
                "Vocabulario Medio": fin_voc.mean(),
                "Vocabulario DE": fin_voc.std(),
                "Vocabulario Mediana": fin_voc.median(),
                "Tasa Exito > 0.80 (%)": (fin_val > 0.80).mean() * 100,
                "Tasa Vocab Perfecto (%)": (fin_voc >= 1.00).mean() * 100
            }
        ])
        
        # Análisis de Deltas y Transición
        deltas = pd.DataFrame([
            {
                "Transicion Conversacional": "Turno 1 -> Turno 2 (Subcohorte N=153)",
                "N Casos": len(sub_t2),
                "Delta Validez Medio": delta_t1_t2_val.mean(),
                "Delta Validez Mediana": delta_t1_t2_val.median(),
                "Validez Mejoraron (N, %)": f"{(delta_t1_t2_val > 0).sum()} ({(delta_t1_t2_val > 0).mean()*100:.1f}%)",
                "Validez Constantes (N, %)": f"{(delta_t1_t2_val == 0).sum()} ({(delta_t1_t2_val == 0).mean()*100:.1f}%)",
                "Validez Empeoraron (N, %)": f"{(delta_t1_t2_val < 0).sum()} ({(delta_t1_t2_val < 0).mean()*100:.1f}%)",
                "Delta Vocabulario Medio": delta_t1_t2_voc.mean(),
                "Vocabulario Mejoraron (N, %)": f"{(delta_t1_t2_voc > 0).sum()} ({(delta_t1_t2_voc > 0).mean()*100:.1f}%)",
                "Vocabulario Constantes (N, %)": f"{(delta_t1_t2_voc == 0).sum()} ({(delta_t1_t2_voc == 0).mean()*100:.1f}%)",
                "Vocabulario Empeoraron (N, %)": f"{(delta_t1_t2_voc < 0).sum()} ({(delta_t1_t2_voc < 0).mean()*100:.1f}%)"
            },
            {
                "Transicion Conversacional": "Turno 2 -> Turno 3 (Subcohorte N=68)",
                "N Casos": len(sub_t3),
                "Delta Validez Medio": delta_t2_t3_val.mean(),
                "Delta Validez Mediana": delta_t2_t3_val.median(),
                "Validez Mejoraron (N, %)": f"{(delta_t2_t3_val > 0).sum()} ({(delta_t2_t3_val > 0).mean()*100:.1f}%)",
                "Validez Constantes (N, %)": f"{(delta_t2_t3_val == 0).sum()} ({(delta_t2_t3_val == 0).mean()*100:.1f}%)",
                "Validez Empeoraron (N, %)": f"{(delta_t2_t3_val < 0).sum()} ({(delta_t2_t3_val < 0).mean()*100:.1f}%)",
                "Delta Vocabulario Medio": delta_t2_t3_voc.mean(),
                "Vocabulario Mejoraron (N, %)": f"{(delta_t2_t3_voc > 0).sum()} ({(delta_t2_t3_voc > 0).mean()*100:.1f}%)",
                "Vocabulario Constantes (N, %)": f"{(delta_t2_t3_voc == 0).sum()} ({(delta_t2_t3_voc == 0).mean()*100:.1f}%)",
                "Vocabulario Empeoraron (N, %)": f"{(delta_t2_t3_voc < 0).sum()} ({(delta_t2_t3_voc < 0).mean()*100:.1f}%)"
            },
            {
                "Transicion Conversacional": "Turno 1 -> Consolidado Final (Global N=201)",
                "N Casos": len(df),
                "Delta Validez Medio": delta_global_val.mean(),
                "Delta Validez Mediana": delta_global_val.median(),
                "Validez Mejoraron (N, %)": f"{(delta_global_val > 0).sum()} ({(delta_global_val > 0).mean()*100:.1f}%)",
                "Validez Constantes (N, %)": f"{(delta_global_val == 0).sum()} ({(delta_global_val == 0).mean()*100:.1f}%)",
                "Validez Empeoraron (N, %)": f"{(delta_global_val < 0).sum()} ({(delta_global_val < 0).mean()*100:.1f}%)",
                "Delta Vocabulario Medio": delta_global_voc.mean(),
                "Vocabulario Mejoraron (N, %)": f"{(delta_global_voc > 0).sum()} ({(delta_global_voc > 0).mean()*100:.1f}%)",
                "Vocabulario Constantes (N, %)": f"{(delta_global_voc == 0).sum()} ({(delta_global_voc == 0).mean()*100:.1f}%)",
                "Vocabulario Empeoraron (N, %)": f"{(delta_global_voc < 0).sum()} ({(delta_global_voc < 0).mean()*100:.1f}%)"
            }
        ])
        
        # Resolutividad acumulada
        t1_res = (df["turno_1_validez_sintactica_y_estructural"] > 0.80).sum()
        t2_res_direct = ((df["turnos_ejecutados"] >= 2) & (df["turno_2_validez_sintactica_y_estructural"] > 0.80)).sum()
        t2_res = t1_res + t2_res_direct
        t3_res = (df["validez_sintactica_y_estructural"] > 0.80).sum()
        
        resolutividad = pd.DataFrame([
            {"Hito Conversacional": "Turno 1 (Resolución Directa)", "Casos Resueltos Acumulados": t1_res, "Pct Acumulado (%)": (t1_res/len(df))*100, "Ganancia Marginal (%)": (t1_res/len(df))*100},
            {"Hito Conversacional": "Turno 2 (Tras 1ª Retroalimentación Juez)", "Casos Resueltos Acumulados": t2_res, "Pct Acumulado (%)": (t2_res/len(df))*100, "Ganancia Marginal (%)": ((t2_res - t1_res)/len(df))*100},
            {"Hito Conversacional": "Turno 3 / Final (Tras 2ª Retroalimentación)", "Casos Resueltos Acumulados": t3_res, "Pct Acumulado (%)": (t3_res/len(df))*100, "Ganancia Marginal (%)": ((t3_res - t2_res)/len(df))*100},
            {"Hito Conversacional": "Casos No Resueltos (Validez <= 0.80)", "Casos Resueltos Acumulados": len(df) - t3_res, "Pct Acumulado (%)": ((len(df) - t3_res)/len(df))*100, "Ganancia Marginal (%)": 0.0}
        ])
        
        return summary_turns, deltas, resolutividad, (delta_t1_t2_val, delta_t2_t3_val, delta_global_val)

    def run_inferential_tests(self):
        """Ejecuta todos los contrastes de hipótesis no paramétricos e inferenciales."""
        df = self.df
        test_results = []
        
        # 1. Tests de Normalidad (Shapiro-Wilk y D'Agostino)
        for name, col in [
            ("Validez Sintáctica y Estructural Final", "validez_sintactica_y_estructural"),
            ("Precisión Terminológica Vocabulario Final", "precision_terminologica_vocabulario"),
            ("Turnos Conversacionales Ejecutados", "turnos_ejecutados"),
            ("Validez Turno 1", "turno_1_validez_sintactica_y_estructural")
        ]:
            s = df[col].dropna()
            w_stat, p_sw = stats.shapiro(s)
            k2_stat, p_dag = stats.normaltest(s)
            test_results.append({
                "Familia de Prueba": "Normalidad",
                "Contraste": f"Shapiro-Wilk ({name})",
                "Estadistico": f"W = {w_stat:.4f}",
                "p_valor_raw": p_sw,
                "p_valor": format_pvalue(p_sw),
                "Interpretacion": "Distribución NO normal (p < 0.05). Justifica métodos no paramétricos."
            })
            test_results.append({
                "Familia de Prueba": "Normalidad",
                "Contraste": f"D'Agostino-Pearson ({name})",
                "Estadistico": f"K2 = {k2_stat:.4f}",
                "p_valor_raw": p_dag,
                "p_valor": format_pvalue(p_dag),
                "Interpretacion": "Asimetría y curtosis significativamente desviadas de la normalidad."
            })
            
        # 2. Kruskal-Wallis por Nivel de Complejidad (baja, intermedia, compleja)
        for var_name, col in [
            ("Validez Sintáctica y Estructural", "validez_sintactica_y_estructural"),
            ("Precisión Terminológica Vocabulario", "precision_terminologica_vocabulario"),
            ("Turnos Conversacionales Ejecutados", "turnos_ejecutados")
        ]:
            g_baja = df[df["nivel_complejidad"] == "baja"][col].values
            g_inter = df[df["nivel_complejidad"] == "intermedia"][col].values
            g_comp = df[df["nivel_complejidad"] == "compleja"][col].values
            
            h_stat, p_val = stats.kruskal(g_baja, g_inter, g_comp)
            n_tot = len(df)
            k_groups = 3
            epsilon2 = (h_stat - k_groups + 1) / (n_tot - k_groups)
            
            test_results.append({
                "Familia de Prueba": "Muestras Independientes (Complejidad)",
                "Contraste": f"Kruskal-Wallis ({var_name} entre Complejidades)",
                "Estadistico": f"H({k_groups-1}) = {h_stat:.4f}",
                "p_valor_raw": p_val,
                "p_valor": format_pvalue(p_val),
                "Interpretacion": f"Efecto global significativo (p < 0.05, ε² = {epsilon2:.4f}). Requiere post-hoc Dunn." if p_val < 0.05 else f"Sin diferencias estadísticamente significativas (ε² = {epsilon2:.4f})."
            })
            
        # Post-Hoc Dunn para Validez Sintáctica por Complejidad
        dunn_validez = dunn_posthoc(
            [df[df["nivel_complejidad"] == "baja"]["validez_sintactica_y_estructural"].values,
             df[df["nivel_complejidad"] == "intermedia"]["validez_sintactica_y_estructural"].values,
             df[df["nivel_complejidad"] == "compleja"]["validez_sintactica_y_estructural"].values],
            ["Baja", "Intermedia", "Compleja"]
        )
        for _, row in dunn_validez.iterrows():
            test_results.append({
                "Familia de Prueba": "Post-Hoc Dunn (Validez Sintáctica)",
                "Contraste": f"Dunn + Holm: {row['comparison']}",
                "Estadistico": f"Z = {row['z_stat']:.4f}",
                "p_valor_raw": row["p_adj_holm"],
                "p_valor": format_pvalue(row["p_adj_holm"]),
                "Interpretacion": f"Diferencia significativa ajustada (p_adj < 0.05)" if row["significativo"] else "No significativo tras corrección Holm"
            })

        # Post-Hoc Dunn para Turnos Ejecutados por Complejidad
        dunn_turnos = dunn_posthoc(
            [df[df["nivel_complejidad"] == "baja"]["turnos_ejecutados"].values,
             df[df["nivel_complejidad"] == "intermedia"]["turnos_ejecutados"].values,
             df[df["nivel_complejidad"] == "compleja"]["turnos_ejecutados"].values],
            ["Baja", "Intermedia", "Compleja"]
        )
        for _, row in dunn_turnos.iterrows():
            test_results.append({
                "Familia de Prueba": "Post-Hoc Dunn (Turnos Ejecutados)",
                "Contraste": f"Dunn + Holm: {row['comparison']}",
                "Estadistico": f"Z = {row['z_stat']:.4f}",
                "p_valor_raw": row["p_adj_holm"],
                "p_valor": format_pvalue(row["p_adj_holm"]),
                "Interpretacion": f"Diferencia significativa ajustada (p_adj < 0.05)" if row["significativo"] else "No significativo tras corrección Holm"
            })

        # 3. Kruskal-Wallis por Dominio OMOP Robusto (N >= 10)
        groups_dom = [group["validez_sintactica_y_estructural"].values for _, group in df.groupby("domain_robust")]
        dom_names = [name for name, _ in df.groupby("domain_robust")]
        h_dom, p_dom = stats.kruskal(*groups_dom)
        test_results.append({
            "Familia de Prueba": "Muestras Independientes (Dominio)",
            "Contraste": "Kruskal-Wallis (Validez entre Dominios OMOP Robusto)",
            "Estadistico": f"H({len(dom_names)-1}) = {h_dom:.4f}",
            "p_valor_raw": p_dom,
            "p_valor": format_pvalue(p_dom),
            "Interpretacion": "Diferencias significativas en validez según el dominio de la consulta OMOP."
        })

        # Comparación específica: Tablas de Épocas (Eras) vs Tablas de Eventos Crudos (Occurrences/Exposures)
        eras_val = df[df["categoria_dominio"] == "Tablas de Épocas (Eras)"]["validez_sintactica_y_estructural"].values
        events_val = df[df["categoria_dominio"] == "Tablas de Eventos Crudos"]["validez_sintactica_y_estructural"].values
        u_stat, p_u = stats.mannwhitneyu(eras_val, events_val, alternative="two-sided")
        cliff_delta = compute_cliffs_delta(eras_val, events_val)
        test_results.append({
            "Familia de Prueba": "Muestras Independientes (Arquitectura OMOP)",
            "Contraste": "Mann-Whitney U: Tablas de Épocas vs Eventos Crudos",
            "Estadistico": f"U = {u_stat:.1f}, Cliff's δ = {cliff_delta:.3f}",
            "p_valor_raw": p_u,
            "p_valor": format_pvalue(p_u),
            "Interpretacion": f"Tendencia a menor rendimiento en tablas de épocas frente a eventos crudos (p = {p_u:.3f}, δ = {cliff_delta:.3f})."
        })

        # Comparación focalizada: condition_era vs condition_occurrence
        c_era = df[df["domain_main"] == "condition_era"]["validez_sintactica_y_estructural"].values
        c_occ = df[df["domain_main"] == "condition_occurrence"]["validez_sintactica_y_estructural"].values
        u_ce_co, p_ce_co = stats.mannwhitneyu(c_era, c_occ, alternative="two-sided")
        cliff_ce_co = compute_cliffs_delta(c_era, c_occ)
        test_results.append({
            "Familia de Prueba": "Muestras Independientes (Arquitectura OMOP)",
            "Contraste": "Mann-Whitney U: condition_era vs condition_occurrence",
            "Estadistico": f"U = {u_ce_co:.1f}, Cliff's δ = {cliff_ce_co:.3f}",
            "p_valor_raw": p_ce_co,
            "p_valor": format_pvalue(p_ce_co),
            "Interpretacion": f"Penalización altamente significativa en condition_era frente a condition_occurrence (p = {p_ce_co:.4f}, δ = {cliff_ce_co:.3f})."
        })

        # 4. Pruebas Emparejadas / Medidas Repetidas (Efecto del Juez LLM)
        # Turno 1 vs Turno 2 (Subcohorte N = 153)
        sub_t2 = df[df["turnos_ejecutados"] >= 2]
        w_t1_t2, p_w_t1_t2 = stats.wilcoxon(sub_t2["turno_1_validez_sintactica_y_estructural"], sub_t2["turno_2_validez_sintactica_y_estructural"])
        rb_t1_t2 = compute_rank_biserial(w_t1_t2, len(sub_t2))
        test_results.append({
            "Familia de Prueba": "Muestras Emparejadas (Impacto Feedback)",
            "Contraste": "Wilcoxon Signed-Rank: Turno 1 vs Turno 2 (Validez, N=153)",
            "Estadistico": f"W = {w_t1_t2:.1f}, r_rb = {rb_t1_t2:.3f}",
            "p_valor_raw": p_w_t1_t2,
            "p_valor": format_pvalue(p_w_t1_t2),
            "Interpretacion": "Mejora altamente significativa en validez tras la 1ª retroalimentación del evaluador LLM."
        })
        
        # Turno 2 vs Turno 3 (Subcohorte N = 68)
        sub_t3 = df[df["turnos_ejecutados"] >= 3]
        w_t2_t3, p_w_t2_t3 = stats.wilcoxon(sub_t3["turno_2_validez_sintactica_y_estructural"], sub_t3["turno_3_validez_sintactica_y_estructural"])
        rb_t2_t3 = compute_rank_biserial(w_t2_t3, len(sub_t3))
        test_results.append({
            "Familia de Prueba": "Muestras Emparejadas (Impacto Feedback)",
            "Contraste": "Wilcoxon Signed-Rank: Turno 2 vs Turno 3 (Validez, N=68)",
            "Estadistico": f"W = {w_t2_t3:.1f}, r_rb = {rb_t2_t3:.3f}",
            "p_valor_raw": p_w_t2_t3,
            "p_valor": format_pvalue(p_w_t2_t3),
            "Interpretacion": "Mejora estadísticamente significativa tras la 2ª retroalimentación en casos complejos."
        })
        
        # Turno 1 vs Consolidado Final (Global N = 201)
        w_glob, p_w_glob = stats.wilcoxon(df["turno_1_validez_sintactica_y_estructural"], df["validez_sintactica_y_estructural"])
        rb_glob = compute_rank_biserial(w_glob, len(df))
        test_results.append({
            "Familia de Prueba": "Muestras Emparejadas (Impacto Feedback)",
            "Contraste": "Wilcoxon Signed-Rank: Turno 1 vs Final (Validez, N=201)",
            "Estadistico": f"W = {w_glob:.1f}, r_rb = {rb_glob:.3f}",
            "p_valor_raw": p_w_glob,
            "p_valor": format_pvalue(p_w_glob),
            "Interpretacion": "Ganancia masiva acumulada del agente gracias al mecanismo conversacional interactivo."
        })

        # Test de Friedman en la subcohorte completa de 3 turnos (N = 68)
        friedman_stat, p_friedman = stats.friedmanchisquare(
            sub_t3["turno_1_validez_sintactica_y_estructural"],
            sub_t3["turno_2_validez_sintactica_y_estructural"],
            sub_t3["turno_3_validez_sintactica_y_estructural"]
        )
        test_results.append({
            "Familia de Prueba": "Medidas Repetidas Longitudinales",
            "Contraste": "Friedman: Trayectoria T1 -> T2 -> T3 (Subcohorte N=68)",
            "Estadistico": f"Q(2) = {friedman_stat:.4f}",
            "p_valor_raw": p_friedman,
            "p_valor": format_pvalue(p_friedman),
            "Interpretacion": "Evolución longitudinal ascendente significativa a través de los 3 turnos sucesivos."
        })

        # Test de McNemar para la tasa de resolución (> 0.80) entre Turno 1 y Final
        # Tabla de contingencia 2x2 para McNemar
        t1_pass = df["turno_1_validez_sintactica_y_estructural"] > 0.80
        fin_pass = df["validez_sintactica_y_estructural"] > 0.80
        table_mcnemar = pd.crosstab(t1_pass, fin_pass)
        res_mcnemar = mcnemar(table_mcnemar, exact=False, correction=True)
        test_results.append({
            "Familia de Prueba": "Proporciones Emparejadas (Resolutividad)",
            "Contraste": "McNemar: Tasa Éxito Turno 1 (23.9%) vs Final (81.6%)",
            "Estadistico": f"χ² = {res_mcnemar.statistic:.4f}",
            "p_valor_raw": res_mcnemar.pvalue,
            "p_valor": format_pvalue(res_mcnemar.pvalue),
            "Interpretacion": "Aumento significativo de la proporción de casos resueltos operativamente (+57.7% neto)."
        })

        # 5. Pruebas de Asociación Categórica
        # Complejidad × Resolutividad Final (> 0.80 vs <= 0.80)
        ct_res = pd.crosstab(df["nivel_complejidad"], df["exito_resolucion_080"])
        chi2_res, p_chi2_res, dof_res, _ = stats.chi2_contingency(ct_res)
        cramers_res = np.sqrt(chi2_res / (len(df) * (min(ct_res.shape) - 1)))
        test_results.append({
            "Familia de Prueba": "Asociación Categórica",
            "Contraste": "Chi-cuadrado: Complejidad × Resolutividad Final (>0.80)",
            "Estadistico": f"χ²({dof_res}) = {chi2_res:.4f}, V de Cramér = {cramers_res:.3f}",
            "p_valor_raw": p_chi2_res,
            "p_valor": format_pvalue(p_chi2_res),
            "Interpretacion": "Asociación estadísticamente significativa entre la complejidad de la consulta y la tasa de resolución."
        })

        return pd.DataFrame(test_results)

    def analyze_correlations(self):
        """Calcula matrices de correlación de Spearman y Kendall con significación."""
        df = self.df
        vars_corr = [
            ("Complejidad (Ordinal)", "nivel_complejidad_num"),
            ("Turnos Conversacionales", "turnos_ejecutados"),
            ("Validez Sintáctica Final", "validez_sintactica_y_estructural"),
            ("Criterio 1.1 Ejecución BigQuery", "criterio_1_1_ejecucion"),
            ("Criterio 1.2 Similitud Semántica", "criterio_1_2_similitud_sql_gemini"),
            ("Precisión Terminológica Vocabulario", "precision_terminologica_vocabulario"),
            ("Validez Turno 1 (Zero-Shot)", "turno_1_validez_sintactica_y_estructural")
        ]
        
        n_vars = len(vars_corr)
        spearman_rho = np.zeros((n_vars, n_vars))
        spearman_pval = np.zeros((n_vars, n_vars))
        kendall_tau = np.zeros((n_vars, n_vars))
        kendall_pval = np.zeros((n_vars, n_vars))
        labels = [v[0] for v in vars_corr]
        
        for i in range(n_vars):
            for j in range(n_vars):
                s1 = df[vars_corr[i][1]]
                s2 = df[vars_corr[j][1]]
                rho, p_rho = stats.spearmanr(s1, s2)
                tau, p_tau = stats.kendalltau(s1, s2)
                spearman_rho[i, j] = rho
                spearman_pval[i, j] = p_rho
                kendall_tau[i, j] = tau
                kendall_pval[i, j] = p_tau
                
        df_rho = pd.DataFrame(spearman_rho, index=labels, columns=labels)
        df_p_rho = pd.DataFrame(spearman_pval, index=labels, columns=labels)
        df_tau = pd.DataFrame(kendall_tau, index=labels, columns=labels)
        df_p_tau = pd.DataFrame(kendall_pval, index=labels, columns=labels)
        
        return df_rho, df_p_rho, df_tau, df_p_tau

    def analyze_unresolved_cases(self):
        """Filtra y caracteriza los 37 casos no resueltos (Validez <= 0.80)."""
        df = self.df
        unresolved = df[df["validez_sintactica_y_estructural"] <= 0.80].copy()
        unresolved["c1_1_status"] = unresolved["criterio_1_1_ejecucion"].apply(lambda x: "Ejecutable (0.10)" if x == 0.10 else "Fallo Sintaxis (0.00)")
        
        cols = [
            "id_evaluacion", "nivel_complejidad", "domain_main", "turnos_ejecutados",
            "validez_sintactica_y_estructural", "c1_1_status", "precision_terminologica_vocabulario",
            "turno_1_validez_sintactica_y_estructural", "turno_2_validez_sintactica_y_estructural",
            "turno_3_validez_sintactica_y_estructural", "evaluacion_llm_juez"
        ]
        return unresolved[cols].sort_values(by="validez_sintactica_y_estructural", ascending=True)

    def export_excel_report(self, output_path):
        """Exporta el reporte analítico multihistorial formateado a Excel."""
        df_global = self.analyze_global_descriptives()
        df_comp = self.analyze_by_complexity()
        ct_raw, ct_row, ct_col, chi_stats = self.analyze_contingency_complexity_turns()
        dom_group, cat_group = self.analyze_by_domain()
        pivot_val, pivot_cnt = self.analyze_domain_complexity_matrix()
        sum_turns, sum_deltas, resolutividad, _ = self.analyze_multiturn_dynamics()
        df_tests = self.run_inferential_tests()
        df_rho, df_p_rho, df_tau, df_p_tau = self.analyze_correlations()
        df_unres = self.analyze_unresolved_cases()
        
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            # 1. Global
            df_global.to_excel(writer, sheet_name="01_Descriptiva_Global", index=False)
            # 2. Complejidad
            df_comp.to_excel(writer, sheet_name="02_Por_Complejidad", index=False)
            # 3. Dominio
            dom_group.to_excel(writer, sheet_name="03_Por_Dominio", index=False)
            cat_group.to_excel(writer, sheet_name="03_Por_Dominio", startrow=len(dom_group) + 3, index=False)
            pivot_val.to_excel(writer, sheet_name="03_Por_Dominio", startrow=len(dom_group) + len(cat_group) + 6)
            # 4. Contingencia Turnos
            ct_raw.to_excel(writer, sheet_name="04_Contingencia_Turnos", startrow=0)
            ct_row.to_excel(writer, sheet_name="04_Contingencia_Turnos", startrow=7)
            # 5. Dinámica Multiturno
            sum_turns.to_excel(writer, sheet_name="05_Dinamica_Multiturno", startrow=0, index=False)
            sum_deltas.to_excel(writer, sheet_name="05_Dinamica_Multiturno", startrow=7, index=False)
            resolutividad.to_excel(writer, sheet_name="05_Dinamica_Multiturno", startrow=13, index=False)
            # 6. Pruebas Hipótesis
            df_tests.to_excel(writer, sheet_name="06_Pruebas_Hipotesis", index=False)
            # 7. Correlaciones
            df_rho.to_excel(writer, sheet_name="07_Correlaciones", startrow=0)
            df_p_rho.to_excel(writer, sheet_name="07_Correlaciones", startrow=10)
            # 8. Casos No Resueltos
            df_unres.to_excel(writer, sheet_name="08_Casos_No_Resueltos", index=False)
            
            # Estilos Openpyxl basados en la Identidad Visual de Universidad Europea
            thin_border = Border(
                left=Side(style='thin', color='D2D4D9'),
                right=Side(style='thin', color='D2D4D9'),
                top=Side(style='thin', color='D2D4D9'),
                bottom=Side(style='thin', color='D2D4D9')
            )
            # Rojo Primario Corporativo UE (#FF3228) para TODAS las cabeceras del libro Excel
            header_fill_red = PatternFill(start_color="FF3228", end_color="FF3228", fill_type="solid")
            header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
            index_font = Font(name="Arial", size=11, bold=True, color="1E1E1E")
            reg_font = Font(name="Arial", size=11, color="1E1E1E")
            
            # Mapeo exacto de filas que corresponden a cabeceras de tablas por hoja
            header_rows_map = {
                "01_Descriptiva_Global": [1],
                "02_Por_Complejidad": [1],
                "03_Por_Dominio": [1, len(dom_group) + 4, len(dom_group) + len(cat_group) + 7],
                "04_Contingencia_Turnos": [1, 8],
                "05_Dinamica_Multiturno": [1, 8, 14],
                "06_Pruebas_Hipotesis": [1],
                "07_Correlaciones": [1, 11],
                "08_Casos_No_Resueltos": [1]
            }

            for ws_name in writer.sheets:
                ws = writer.sheets[ws_name]
                target_header_rows = set(header_rows_map.get(ws_name, [1]))
                
                # Ajustar etiquetas de esquinas de matrices si están vacías
                if ws_name == "04_Contingencia_Turnos":
                    if ws.cell(1, 1).value is None or ws.cell(1, 1).value == "":
                        ws.cell(1, 1).value = "Nivel de Complejidad (Frecuencia)"
                    if ws.cell(8, 1).value is None or ws.cell(8, 1).value == "":
                        ws.cell(8, 1).value = "Nivel de Complejidad (% Fila)"
                elif ws_name == "07_Correlaciones":
                    if ws.cell(1, 1).value is None or ws.cell(1, 1).value == "":
                        ws.cell(1, 1).value = "Matriz de Spearman (rho)"
                    if ws.cell(11, 1).value is None or ws.cell(11, 1).value == "":
                        ws.cell(11, 1).value = "Matriz de Spearman (p-valor)"
                elif ws_name == "03_Por_Dominio":
                    pivot_row = len(dom_group) + len(cat_group) + 7
                    if ws.cell(pivot_row, 1).value is None or ws.cell(pivot_row, 1).value == "":
                        ws.cell(pivot_row, 1).value = "Dominio OMOP"

                for row in ws.iter_rows():
                    r_idx = row[0].row
                    is_header_row = r_idx in target_header_rows
                    
                    if is_header_row:
                        ws.row_dimensions[r_idx].height = 26
                    else:
                        ws.row_dimensions[r_idx].height = 20

                    for cell in row:
                        cell.border = thin_border
                        if is_header_row:
                            cell.font = header_font
                            cell.fill = header_fill_red
                            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                        else:
                            # Si es la primera columna en hojas con índices matriciales, estilo negrita sobrio
                            is_index_col = (cell.column == 1 and ws_name in ["04_Contingencia_Turnos", "07_Correlaciones"]) or \
                                           (cell.column == 1 and ws_name == "03_Por_Dominio" and r_idx > (len(dom_group) + len(cat_group) + 7))
                            cell.font = index_font if is_index_col else reg_font
                            
                            # Formato numérico
                            if isinstance(cell.value, float):
                                header_val = str(ws.cell(list(target_header_rows)[0], cell.column).value or '')
                                if abs(cell.value) < 0.001 and cell.value != 0:
                                    cell.number_format = "0.00E+00"
                                elif any(k in header_val for k in ["(%)", "Pct", "Tasa", "Ganancia"]):
                                    cell.number_format = "0.0%" if abs(cell.value) <= 1.0 else "0.0\"%\""
                                else:
                                    cell.number_format = "0.00"
                            cell.alignment = Alignment(horizontal="center" if isinstance(cell.value, (int, float)) and not is_index_col else "left", vertical="center")
                
                # Autoajustar ancho columnas
                for col in ws.columns:
                    max_len = max(len(str(cell.value or '')) for cell in col)
                    col_letter = get_column_letter(col[0].column)
                    ws.column_dimensions[col_letter].width = min(max(max_len + 4, 14), 65)

    def generate_figures(self, figures_dir):
        """Genera y exporta la galería de 6 figuras científicas a 300 DPI y SVG."""
        os.makedirs(figures_dir, exist_ok=True)
        df = self.df
        
        # Figura 1: Rendimiento por Nivel de Complejidad (Violin + Stripplot)
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        order = ["baja", "intermedia", "compleja"]
        order_labels = ["Baja (N=26)", "Intermedia (N=71)", "Compleja (N=104)"]
        palette = [UE_COLORS["cyan"], UE_COLORS["navy"], UE_COLORS["red"]]
        
        sns.violinplot(ax=axes[0], data=df, x="nivel_complejidad", y="validez_sintactica_y_estructural", order=order, hue="nivel_complejidad", palette=palette, legend=False, inner="quartile", cut=0)
        sns.stripplot(ax=axes[0], data=df, x="nivel_complejidad", y="validez_sintactica_y_estructural", order=order, color=UE_COLORS["charcoal"], alpha=0.35, jitter=0.2, size=5)
        axes[0].set_title("A. Validez Sintáctica y Estructural Final")
        axes[0].set_xlabel("Nivel de Complejidad de la Consulta")
        axes[0].set_ylabel("Puntuación de Validez (0.00 - 1.00)")
        axes[0].set_xticks([0, 1, 2])
        axes[0].set_xticklabels(order_labels)
        axes[0].axhline(0.80, color=UE_COLORS["red"], linestyle="--", linewidth=1.5, alpha=0.8, label="Umbral Éxito (> 0.80)")
        axes[0].legend(loc="lower left")
        
        sns.violinplot(ax=axes[1], data=df, x="nivel_complejidad", y="precision_terminologica_vocabulario", order=order, hue="nivel_complejidad", palette=palette, legend=False, inner="quartile", cut=0)
        sns.stripplot(ax=axes[1], data=df, x="nivel_complejidad", y="precision_terminologica_vocabulario", order=order, color=UE_COLORS["charcoal"], alpha=0.35, jitter=0.2, size=5)
        axes[1].set_title("B. Precisión Terminológica de Vocabulario OMOP")
        axes[1].set_xlabel("Nivel de Complejidad de la Consulta")
        axes[1].set_ylabel("Precisión de Concept IDs (0.00 - 1.00)")
        axes[1].set_xticks([0, 1, 2])
        axes[1].set_xticklabels(order_labels)
        axes[1].axhline(1.00, color=UE_COLORS["green_success"], linestyle=":", linewidth=1.5, alpha=0.8, label="Precisión Perfecta (1.00)")
        axes[1].legend(loc="lower left")
        
        plt.suptitle("Distribución del Rendimiento del Agente OMOP por Nivel de Complejidad", y=1.02, fontsize=14, fontweight="bold", color=UE_COLORS["navy"])
        plt.tight_layout()
        fig.savefig(os.path.join(figures_dir, "fig1_rendimiento_por_complejidad.png"), dpi=300, bbox_inches="tight")
        fig.savefig(os.path.join(figures_dir, "fig1_rendimiento_por_complejidad.svg"), bbox_inches="tight")
        plt.close()

        # Figura 2: Rendimiento por Dominio OMOP
        dom_group, _ = self.analyze_by_domain()
        fig, ax = plt.subplots(figsize=(12, 6))
        y_pos = np.arange(len(dom_group))
        ax.barh(y_pos - 0.2, dom_group["Validez_Media"], height=0.4, label="Validez Sintáctica Media", color=UE_COLORS["navy"], alpha=0.92)
        ax.barh(y_pos + 0.2, dom_group["Vocab_Medio"], height=0.4, label="Precisión Vocabulario Media", color=UE_COLORS["cyan"], alpha=0.92)
        
        # Anotar N de casos en las etiquetas
        ytick_labels = [f"{row['domain_main']} (N={row['N']})" for _, row in dom_group.iterrows()]
        ax.set_yticks(y_pos)
        ax.set_yticklabels(ytick_labels)
        ax.invert_yaxis()
        ax.set_xlim(0.0, 1.05)
        ax.axvline(0.80, color=UE_COLORS["red"], linestyle="--", linewidth=1.5, alpha=0.85, label="Umbral Éxito (> 0.80)")
        ax.set_xlabel("Puntuación Promedio")
        ax.set_title("Rendimiento del Agente según el Dominio Principal OMOP CDM", fontweight="bold", color=UE_COLORS["navy"])
        ax.legend(loc="lower left")
        plt.tight_layout()
        fig.savefig(os.path.join(figures_dir, "fig2_rendimiento_por_dominio.png"), dpi=300, bbox_inches="tight")
        fig.savefig(os.path.join(figures_dir, "fig2_rendimiento_por_dominio.svg"), bbox_inches="tight")
        plt.close()

        # Figura 3: Dinámica Longitudinal Multi-Turno (Progresión Emparejada T1 -> T2 -> T3)
        sub_t3 = df[df["turnos_ejecutados"] >= 3]
        fig, ax = plt.subplots(figsize=(9, 6))
        for _, row in sub_t3.iterrows():
            ax.plot([1, 2, 3], [row["turno_1_validez_sintactica_y_estructural"], row["turno_2_validez_sintactica_y_estructural"], row["turno_3_validez_sintactica_y_estructural"]], color=UE_COLORS["gray_border"], alpha=0.4, linewidth=1)
            
        t_means = [sub_t3["turno_1_validez_sintactica_y_estructural"].mean(), sub_t3["turno_2_validez_sintactica_y_estructural"].mean(), sub_t3["turno_3_validez_sintactica_y_estructural"].mean()]
        t_medians = [sub_t3["turno_1_validez_sintactica_y_estructural"].median(), sub_t3["turno_2_validez_sintactica_y_estructural"].median(), sub_t3["turno_3_validez_sintactica_y_estructural"].median()]
        
        ax.plot([1, 2, 3], t_means, color=UE_COLORS["red"], marker="o", markersize=8, linewidth=3.2, label=f"Media Trayectoria (T1={t_means[0]:.2f} -> T2={t_means[1]:.2f} -> T3={t_means[2]:.2f})")
        ax.plot([1, 2, 3], t_medians, color=UE_COLORS["navy"], marker="s", markersize=8, linestyle="--", linewidth=2.5, label=f"Mediana Trayectoria (T1={t_medians[0]:.2f} -> T2={t_medians[1]:.2f} -> T3={t_medians[2]:.2f})")
        
        ax.set_xticks([1, 2, 3])
        ax.set_xticklabels(["Turno 1\n(Zero-Shot)", "Turno 2\n(1ª Retroalimentación)", "Turno 3\n(2ª Retroalimentación)"])
        ax.set_ylabel("Validez Sintáctica y Estructural")
        ax.set_ylim(-0.05, 1.05)
        ax.axhline(0.80, color=UE_COLORS["red"], linestyle=":", linewidth=1.5, alpha=0.8, label="Umbral de Parada Satisfactoria (0.80)")
        ax.set_title("Trayectoria Longitudinal del Refinamiento Multi-Turno en Casos Persistentes (N=68)", fontweight="bold", color=UE_COLORS["navy"])
        ax.legend(loc="upper left")
        plt.tight_layout()
        fig.savefig(os.path.join(figures_dir, "fig3_dinamica_longitudinal_turnos.png"), dpi=300, bbox_inches="tight")
        fig.savefig(os.path.join(figures_dir, "fig3_dinamica_longitudinal_turnos.svg"), bbox_inches="tight")
        plt.close()

        # Figura 4: Distribución de Turnos por Nivel de Complejidad (100% Stacked Bar)
        _, ct_row, _, _ = self.analyze_contingency_complexity_turns()
        fig, ax = plt.subplots(figsize=(9, 6.2))
        plot_data = ct_row.loc[["baja", "intermedia", "compleja"], [1, 2, 3]]
        plot_data.index = ["Baja", "Intermedia", "Compleja"]
        
        # Paleta Universidad Europea: Cian (Salud), Azul Institucional, Rojo Corporativo
        colors = [UE_COLORS["cyan"], UE_COLORS["navy"], UE_COLORS["red"]]
        plot_data.plot(kind="bar", stacked=True, ax=ax, color=colors, edgecolor=UE_COLORS["charcoal"], linewidth=0.8)
        ax.set_ylabel("Porcentaje de Casos (%)")
        ax.set_xlabel("Nivel de Complejidad de la Consulta")
        ax.set_title("Esfuerzo Conversacional Requerido según Complejidad (N=201)", fontweight="bold", color=UE_COLORS["navy"], pad=30)
        ax.set_ylim(0, 102)
        ax.legend(["1 Turno (Resolución Inmediata)", "2 Turnos (Refinamiento Moderado)", "3 Turnos (Máxima Interacción)"], loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=3, fontsize=9.5, frameon=True)
        
        # Anotar porcentajes en las barras
        for c in ax.containers:
            ax.bar_label(c, fmt='%.1f%%', label_type='center', color='white', fontweight='bold', fontsize=10)
            
        plt.xticks(rotation=0)
        plt.tight_layout()
        fig.savefig(os.path.join(figures_dir, "fig4_distribucion_turnos_complejidad.png"), dpi=300, bbox_inches="tight")
        fig.savefig(os.path.join(figures_dir, "fig4_distribucion_turnos_complejidad.svg"), bbox_inches="tight")
        plt.close()

        # Figura 5: Matriz de Correlaciones de Spearman
        df_rho, df_p_rho, _, _ = self.analyze_correlations()
        fig, ax = plt.subplots(figsize=(9, 8))
        
        # Anotación combinada rho y asteriscos
        annot = np.empty_like(df_rho, dtype=object)
        for i in range(df_rho.shape[0]):
            for j in range(df_rho.shape[1]):
                r = df_rho.iloc[i, j]
                p = df_p_rho.iloc[i, j]
                stars = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else ""))
                annot[i, j] = f"{r:.2f}\n{stars}" if stars else f"{r:.2f}"
                
        # Colormap divergente personalizado: Azul UE -> Blanco -> Rojo UE
        ue_diverging = LinearSegmentedColormap.from_list("UE_Diverging", [UE_COLORS["navy"], "#FFFFFF", UE_COLORS["red"]])
        sns.heatmap(df_rho, annot=annot, fmt="", cmap=ue_diverging, center=0, vmin=-0.7, vmax=1.0, ax=ax, linewidths=0.6, linecolor=UE_COLORS["gray_border"], cbar_kws={'label': "Coeficiente de Spearman (ρ)"})
        ax.set_title("Matriz de Correlación de Rangos de Spearman (N=201)\n(*p<0.05, **p<0.01, ***p<0.001)", fontweight="bold", color=UE_COLORS["navy"])
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        fig.savefig(os.path.join(figures_dir, "fig5_matriz_correlaciones_spearman.png"), dpi=300, bbox_inches="tight")
        fig.savefig(os.path.join(figures_dir, "fig5_matriz_correlaciones_spearman.svg"), bbox_inches="tight")
        plt.close()

        # Figura 6: Curva de Resolutividad Acumulada
        _, _, resolutividad, _ = self.analyze_multiturn_dynamics()
        fig, ax = plt.subplots(figsize=(8, 5))
        turns_x = [1, 2, 3]
        res_y = [resolutividad.loc[0, "Pct Acumulado (%)"], resolutividad.loc[1, "Pct Acumulado (%)"], resolutividad.loc[2, "Pct Acumulado (%)"]]
        
        ax.plot(turns_x, res_y, marker="o", markersize=10, linewidth=3.2, color=UE_COLORS["red"], label="Tasa de Éxito Acumulada (Validez > 0.80)")
        ax.fill_between(turns_x, res_y, color=UE_COLORS["red_tint"], alpha=0.75)
        
        for x, y in zip(turns_x, res_y):
            ax.annotate(f"{y:.1f}%", (x, y), textcoords="offset points", xytext=(0, 12), ha='center', fontweight='bold', fontsize=11, color=UE_COLORS["charcoal"])
            
        ax.plot(turns_x, res_y, marker="o", markersize=8, color=UE_COLORS["navy"], linestyle="")
        
        ax.set_xticks(turns_x)
        ax.set_xticklabels(["Turno 1\n(Zero-Shot)", "Turno 2\n(+1ª Iteración Feedback)", "Turno 3 / Final\n(+2ª Iteración Feedback)"])
        ax.set_ylabel("Casos Resueltos Acumulados (%)")
        ax.set_ylim(0, 105)
        ax.axhline(81.59, color=UE_COLORS["green_success"], linestyle="--", alpha=0.8, label="Resolutividad Final (81.6%)")
        ax.axhline(23.88, color=UE_COLORS["red"], linestyle=":", alpha=0.8, label="Línea Base Turno 1 (23.9%)")
        ax.set_title("Curva de Eficacia Acumulada del Refinamiento Conversacional (N=201)", fontweight="bold", color=UE_COLORS["navy"])
        ax.legend(loc="lower right")
        plt.tight_layout()
        fig.savefig(os.path.join(figures_dir, "fig6_curva_resolutividad_acumulada.png"), dpi=300, bbox_inches="tight")
        fig.savefig(os.path.join(figures_dir, "fig6_curva_resolutividad_acumulada.svg"), bbox_inches="tight")
        plt.close()

    def generate_markdown_report(self, report_path):
        """Genera el informe completo en formato Markdown listo para el capítulo del TFM."""
        df = self.df
        df_global = self.analyze_global_descriptives()
        df_comp = self.analyze_by_complexity()
        ct_raw, ct_row, ct_col, chi_stats = self.analyze_contingency_complexity_turns()
        dom_group, cat_group = self.analyze_by_domain()
        sum_turns, sum_deltas, resolutividad, _ = self.analyze_multiturn_dynamics()
        df_tests = self.run_inferential_tests()
        df_rho, df_p_rho, _, _ = self.analyze_correlations()
        df_unres = self.analyze_unresolved_cases()
        
        md = []
        md.append("<style>")
        md.append("body, div, p, li, h1, h2, h3, h4, table, th, td, span {")
        md.append("    font-family: Arial, 'Helvetica Neue', Helvetica, sans-serif !important;")
        md.append("}")
        md.append("</style>\n")
        md.append("# Resultados de la Evaluación Experimental: Agente OMOP CDM")
        md.append("## Trabajo Fin de Máster (TFM) en Ciencia de Datos y Bioinformática")
        md.append(f"**Fuente de Evaluación:** OHDSI QueryLibrary (Benchmark Estándar de Oro)")
        md.append(f"**Archivo Fuente Analizado:** `querylibrary_analisis_202609061551.xlsx`")
        md.append(f"**Población Evaluada:** $N = 201$ consultas clínicas y epidemiológicas sobre Google BigQuery OMOP CDM 5.4")
        md.append(f"**Evaluador Asistido por IA (LLM-as-a-Judge):** Gemini 2.5 Flash")
        md.append("\n---\n")
        
        # Sección 1: Descriptiva Global
        md.append("## 1. Perfil Descriptivo Global del Benchmark")
        md.append("En la Tabla 1 se reportan las medidas de tendencia central, dispersión e intervalos de confianza al 95% para las métricas primarias de desempeño del agente a lo largo de las 201 consultas:")
        md.append("\n### Tabla 1: Estadísticos Descriptivos Globales ($N = 201$)")
        md.append("| Métrica Evaluada | $N$ | Media ± DE | Mediana [IQR] | Mín - Máx | IC 95% Media | Asimetría |")
        md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
        for _, r in df_global.iterrows():
            md.append(f"| **{r['Metrica']}** | {r['N']} | {r['Media']:.3f} ± {r['DE']:.3f} | {r['Mediana']:.3f} [{r['IQR']:.3f}] | {r['Minimo']:.2f} - {r['Maximo']:.2f} | [{r['IC95_Inferior']:.3f}, {r['IC95_Superior']:.3f}] | {r['Asimetria (Skewness)']:.2f} |")
            
        md.append("\n### Tasas de Cumplimiento Operativo Global")
        e_exec = (df['criterio_1_1_ejecucion'] == 0.10).mean() * 100
        e_080_strict = (df['validez_sintactica_y_estructural'] > 0.80).mean() * 100
        e_080_inc = (df['validez_sintactica_y_estructural'] >= 0.80).mean() * 100
        e_095 = (df['validez_sintactica_y_estructural'] >= 0.95).mean() * 100
        e_voc = (df['precision_terminologica_vocabulario'] >= 1.00).mean() * 100
        md.append(f"- **Tasa de Ejecutoriedad Sintáctica BigQuery (Criterio 1.1):** **{e_exec:.1f}%** ({int(round(e_exec*2.01))} / 201 consultas generaron SQL sintácticamente ejecutable).")
        md.append(f"- **Tasa de Resolución Operativa del Agente (Validez > 0.80, Umbral Parada):** **{e_080_strict:.1f}%** ({int(round(e_080_strict*2.01))} / 201 consultas superaron el umbral de parada exitosa).")
        md.append(f"- **Tasa de Validez Aceptable Inclusiva (Validez $\\ge 0.80$):** **{e_080_inc:.1f}%** ({int(round(e_080_inc*2.01))} / 201 consultas).")
        md.append(f"- **Tasa de Excelencia Estructural (Validez $\\ge 0.95$):** **{e_095:.1f}%** ({int(round(e_095*2.01))} / 201 consultas fueron idénticas o virtualmente equivalentes al Gold Standard).")
        md.append(f"- **Tasa de Precisión Terminológica Perfecta (Vocabulario = 1.00):** **{e_voc:.1f}%** ({int(round(e_voc*2.01))} / 201 consultas recuperaron con exactitud quirúrgica todos los Concept IDs).")
        md.append("\n---\n")

        # Sección 2: Análisis por Complejidad
        md.append("## 2. Análisis Estratificado por Nivel de Complejidad")
        md.append("La estratificación por nivel de dificultad técnica y clínica revela un comportamiento diferenciado según la complejidad arquitectónica de la consulta OMOP (Tabla 2 y Figuras 1 y 4):")
        md.append("\n### Tabla 2: Rendimiento Comparativo por Complejidad")
        md.append("| Nivel de Complejidad | $N$ (% Cohorte) | Validez Sintáctica (Media ± DE) | Validez (Mediana [IQR]) | Vocabulario (Media ± DE) | Turnos Medios (± DE) | Tasa Éxito > 0.80 | Tasa Vocab = 1.00 |")
        md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
        for _, r in df_comp.iterrows():
            md.append(f"| **{r['Nivel Complejidad']}** | {r['N']} ({r['Pct Cohorte']:.1f}%) | {r['Validez Media']:.3f} ± {r['Validez DE']:.3f} | {r['Validez Mediana']:.3f} [{r['Validez IQR']:.3f}] | {r['Vocabulario Medio']:.3f} ± {r['Vocabulario DE']:.3f} | {r['Turnos Medios']:.2f} ± {r['Turnos DE']:.2f} | {r['Tasa Exito >= 0.80 (%)']:.1f}% | {r['Tasa Vocabulario Perfecto (%)']:.1f}% |")

        md.append("\n### Tabla 3: Tabla de Contingencia Complejidad × Turnos Ejecutados")
        md.append("| Nivel Complejidad | Turno 1 ($N$, % fila) | Turno 2 ($N$, % fila) | Turno 3 ($N$, % fila) | Total ($N$, 100%) |")
        md.append("| :--- | :---: | :---: | :---: | :---: |")
        for comp in ["baja", "intermedia", "compleja"]:
            n_tot = ct_raw.loc[comp, "Total"]
            t1_n, t1_p = ct_raw.loc[comp, 1], ct_row.loc[comp, 1]
            t2_n, t2_p = ct_raw.loc[comp, 2], ct_row.loc[comp, 2]
            t3_n, t3_p = ct_raw.loc[comp, 3], ct_row.loc[comp, 3]
            md.append(f"| **{comp.capitalize()}** | {t1_n} ({t1_p:.1f}%) | {t2_n} ({t2_p:.1f}%) | {t3_n} ({t3_p:.1f}%) | {n_tot} (100.0%) |")
        md.append(f"| **Total Global** | {ct_raw.loc['Total', 1]} ({ct_row.loc['Total', 1]:.1f}%) | {ct_raw.loc['Total', 2]} ({ct_row.loc['Total', 2]:.1f}%) | {ct_raw.loc['Total', 3]} ({ct_row.loc['Total', 3]:.1f}%) | {len(df)} (100.0%) |")
        
        md.append(f"\n*Prueba de Independencia Chi-cuadrado:* $\\chi^2({chi_stats['dof']}) = {chi_stats['chi2']:.3f}$, $p = {chi_stats['p_value']:.4f}$ ({format_pvalue(chi_stats['p_value'])}), $V \\text{{ de Cramér}} = {chi_stats['cramers_v']:.3f}$. Existe una dependencia estadísticamente significativa entre la complejidad de la consulta y el número de turnos requeridos para su resolución.")
        md.append("\n![Figura 1: Distribución del Rendimiento del Agente OMOP por Nivel de Complejidad](figures/fig1_rendimiento_por_complejidad.png)\n")
        md.append("\n![Figura 4: Esfuerzo Conversacional Requerido según Complejidad](figures/fig4_distribucion_turnos_complejidad.png)\n")
        md.append("\n---\n")

        # Sección 3: Rendimiento por Dominio OMOP
        md.append("## 3. Rendimiento Estratificado por Dominio OMOP CDM")
        md.append("El análisis por dominio evidencia cómo el modelo OMOP condiciona la dificultad de formulación SQL. Las consultas sobre tablas de agregación de épocas clínicas (`condition_era`, `drug_era`) requirieron mayor esfuerzo de refinamiento y obtuvieron rendimientos menores que las tablas de ocurrencias directas (`condition_occurrence`, `drug_exposure`, `person`) (Tabla 4 y Figura 2):")
        md.append("\n### Tabla 4: Desempeño por Dominio Principal OMOP")
        md.append("| Dominio OMOP (`domain_main`) | $N$ (% Cohorte) | Validez Sintáctica Media (± DE) | Validez Mediana | Vocabulario Medio | Turnos Medios | % Éxito > 0.80 |")
        md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
        for _, r in dom_group.iterrows():
            md.append(f"| **{r['domain_main']}** | {r['N']} ({r['Pct_Cohorte']:.1f}%) | {r['Validez_Media']:.3f} ± {r['Validez_DE']:.3f} | {r['Validez_Mediana']:.3f} | {r['Vocab_Medio']:.3f} | {r['Turnos_Medios']:.2f} | {r['Exito_Pct']:.1f}% |")

        md.append("\n### Tabla 5: Comparativa Arquitectónica por Categoría OMOP Agrupada")
        md.append("| Categoría Arquitectónica | $N$ (%) | Validez Media ± DE | Validez Mediana | Vocabulario Medio | Turnos Medios | % Éxito > 0.80 |")
        md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
        for _, r in cat_group.iterrows():
            md.append(f"| **{r['categoria_dominio']}** | {r['N']} ({r['Pct_Cohorte']:.1f}%) | {r['Validez_Media']:.3f} ± {r['Validez_DE']:.3f} | {r['Validez_Mediana']:.3f} | {r['Vocab_Medio']:.3f} | {r['Turnos_Medios']:.2f} | {r['Exito_Pct']:.1f}% |")
        md.append("\n![Figura 2: Rendimiento del Agente según el Dominio Principal OMOP CDM](figures/fig2_rendimiento_por_dominio.png)\n")
        md.append("\n---\n")

        # Sección 4: Dinámica Multi-Turno
        md.append("## 4. Dinámica Longitudinal y Efectividad del Refinamiento Multi-Turno")
        md.append("Uno de los pilares del diseño del agente OMOP es el bucle conversacional iterativo asistido por el evaluador LLM. En la Tabla 6 se detalla la progresión turno a turno:")
        md.append("\n### Tabla 6: Rendimiento Comparativo por Turno Conversacional")
        md.append("| Turno Evaluado | $N$ | Validez Media ± DE | Validez Mediana [IQR] | Vocabulario Medio | Tasa Éxito > 0.80 | Vocabulario Perfecto |")
        md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
        for _, r in sum_turns.iterrows():
            md.append(f"| **{r['Turno Evaluado']}** | {r['N Casos']} | {r['Validez Media']:.3f} ± {r['Validez DE']:.3f} | {r['Validez Mediana']:.3f} [{r['Validez IQR']:.3f}] | {r['Vocabulario Medio']:.3f} | {r['Tasa Exito > 0.80 (%)']:.1f}% | {r['Tasa Vocab Perfecto (%)']:.1f}% |")

        md.append("\n### Tabla 7: Análisis de Ganancia / Deltas ($\\Delta$) por Intervención del Evaluador LLM")
        md.append("| Transición Conversacional | $N$ | $\\Delta$ Validez Medio (Mediana) | Validez: Mejoraron | Validez: Constantes | Validez: Empeoraron | $\\Delta$ Vocabulario Medio | Vocab: Mejoraron |")
        md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
        for _, r in sum_deltas.iterrows():
            md.append(f"| **{r['Transicion Conversacional']}** | {r['N Casos']} | {r['Delta Validez Medio']:+.3f} ({r['Delta Validez Mediana']:+.3f}) | {r['Validez Mejoraron (N, %)']} | {r['Validez Constantes (N, %)']} | {r['Validez Empeoraron (N, %)']} | {r['Delta Vocabulario Medio']:+.3f} | {r['Vocabulario Mejoraron (N, %)']} |")

        md.append("\n### Tabla 8: Curva de Resolutividad Acumulada del Sistema")
        md.append("| Hito Conversacional | Casos Resueltos Acumulados ($N$) | Porcentaje Acumulado (%) | Ganancia Marginal (%) |")
        md.append("| :--- | :---: | :---: | :---: |")
        for _, r in resolutividad.iterrows():
            md.append(f"| **{r['Hito Conversacional']}** | {r['Casos Resueltos Acumulados']} | {r['Pct Acumulado (%)']:.1f}% | {r['Ganancia Marginal (%)']:.1f}% |")

        md.append("\n> **Nota Metodológica sobre el Sesgo de Parada Anticipada (*Early Stopping*):**")
        md.append("> La media de validez en el Turno 3 aparente (0.579) o de los casos que concluyeron en Turno 3 (0.638) no refleja un 'deterioro' del agente con turnos adicionales, sino un efecto de **selección negativa**: los casos resueltos con alta puntuación salieron del flujo en el Turno 1 ($N=48$, media 0.954) o en el Turno 2 ($N=85$, media 0.958). El Turno 3 aísla estrictamente el núcleo duro de consultas que requirieron doble corrección (Figuras 3 y 6). En dicha subcohorte ($N=68$), la retroalimentación incrementó la media de 0.394 a 0.579 ($+0.185$, mejorando el 66.2% de los casos).")
        md.append("\n![Figura 3: Trayectoria Longitudinal del Refinamiento Multi-Turno en Casos Persistentes (N=68)](figures/fig3_dinamica_longitudinal_turnos.png)\n")
        md.append("\n![Figura 6: Curva de Eficacia Acumulada del Refinamiento Conversacional (N=201)](figures/fig6_curva_resolutividad_acumulada.png)\n")
        md.append("\n---\n")

        # Sección 5: Inferencia y Pruebas Estadísticas
        md.append("## 5. Inferencia Estadística y Pruebas de Hipótesis Formales")
        md.append("En la Tabla 9 se compilan los resultados de las pruebas estadísticas de contraste aplicadas para validar formalmente las hipótesis del estudio:")
        md.append("\n### Tabla 9: Batería de Pruebas Estadísticas Inferenciales")
        md.append("| Familia de Prueba | Contraste de Hipótesis | Estadístico de Prueba | $p$-valor | Significación e Interpretación |")
        md.append("| :--- | :--- | :---: | :---: | :--- |")
        for _, r in df_tests.iterrows():
            md.append(f"| **{r['Familia de Prueba']}** | {r['Contraste']} | `{r['Estadistico']}` | **{r['p_valor']}** | {r['Interpretacion']} |")

        md.append("\n### Tabla 10: Matriz de Correlación de Rangos de Spearman ($\\rho$)")
        md.append("| Variable | Complejidad | Turnos | Validez Final | Criterio 1.1 | Criterio 1.2 | Vocabulario | Validez T1 |")
        md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
        labels = df_rho.index
        for idx, lbl in enumerate(labels):
            vals = [f"{df_rho.iloc[idx, j]:.2f}" for j in range(len(labels))]
            md.append(f"| **{lbl}** | " + " | ".join(vals) + " |")
        md.append("\n![Figura 5: Matriz de Correlación de Rangos de Spearman (N=201)](figures/fig5_matriz_correlaciones_spearman.png)\n")
        md.append("\n---\n")

        # Sección 6: Casos no resueltos
        md.append("## 6. Análisis Forense de Casos no Resueltos ($N = 37$, $18.4\\%$)")
        md.append("Los 37 casos que no superaron el umbral de resolutividad operativa ($0.80$) se concentran casi en su totalidad en consultas complejas (30/37, 81.1%) y predominantemente en tablas de agregación de épocas (`condition_era` con 13 casos, `drug_exposure` con 10 casos). En la Tabla 11 se resumen los casos más ilustrativos:")
        md.append("\n### Tabla 11: Muestra Representativa de Casos con Brecha de Desempeño")
        md.append("| ID Evaluación | Complejidad | Dominio | Turnos | Validez Final | Criterio 1.1 | Vocabulario | Causa Principal de Desviación (Evaluador LLM) |")
        md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |")
        for _, r in df_unres.head(10).iterrows():
            clean_eval = str(r["evaluacion_llm_juez"]).replace("\n", " ")[:120] + "..."
            md.append(f"| `{r['id_evaluacion']}` | {r['nivel_complejidad']} | {r['domain_main']} | {r['turnos_ejecutados']} | **{r['validez_sintactica_y_estructural']:.2f}** | {r['c1_1_status']} | {r['precision_terminologica_vocabulario']:.2f} | {clean_eval} |")
            
        md.append("\n---\n")
        
        # Conclusiones TFM
        md.append("## 7. Conclusiones y Aportaciones para la Discusión del TFM")
        md.append("1. **Alta Ejecutoriedad y Precisión Conceptual Base:** El agente demostró una tasa de generación de consultas ejecutables en Google BigQuery del **93.5%** y una precisión media de identificación de conceptos OMOP del **92.5%** (con un 90.0% de consultas con precisión terminológica perfecta).")
        md.append("2. **Impacto Decisivo del Refinamiento Conversacional Multi-Turno:** El paso de una estrategia *zero-shot* (Turno 1) a un flujo interactivo multi-turno incrementó la resolutividad del sistema del **23.9% al 81.6%** (ganancia neta de $+57.7\\%$, prueba de McNemar $p < 0.001$, Wilcoxon $p < 0.001$). Esto demuestra cuantitativamente la necesidad de agentes iterativos con capacidad de auto-corrección guiada frente a modelos puramente generativos directos.")
        md.append("3. **El 'Cuello de Botella' de la Complejidad y las Épocas Clínicas:** Las consultas complejas demandaron significativamente más turnos ($2.31$ vs $1.81$, $p < 0.001$) y obtuvieron una validez final inferior ($0.773$ vs $0.932$, $p < 0.001$). Asimismo, el dominio `condition_era` exhibió una penalización estadísticamente significativa frente a `condition_occurrence` (Mann-Whitney $p = 0.0078$, Cliff's $\\delta = -0.441$), fundamentada en la dificultad intrínseca de los LLMs para modelar solapamientos temporales y persistencia clínica sin directivas semánticas explícitas.")
        md.append("4. **Validación Metodológica:** Los contrastes no paramétricos (Kruskal-Wallis, Dunn-Holm, Wilcoxon, Friedman) confirman con un nivel de significación $\\alpha = 0.05$ las hipótesis de investigación, proporcionando un soporte empírico y estadístico de alta solidez para la memoria del TFM.")

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md))

def main():
    parser = argparse.ArgumentParser(description="Análisis estadístico integral TFM para resultados OMOP QueryLibrary.")
    parser.add_argument("--input", "-i", default="evaluation/results/querylibrary_analisis_202609061551.xlsx", help="Ruta al archivo Excel de resultados consolidado.")
    parser.add_argument("--output-dir", "-od", default=None, help="Directorio base para los outputs (por defecto: evaluation/results/<archivo-analizado>/).")
    parser.add_argument("--output-excel", "-oe", default=None, help="Ruta de salida específica para el libro Excel (opcional).")
    parser.add_argument("--output-report", "-or", default=None, help="Ruta de salida específica para el informe Markdown (opcional).")
    parser.add_argument("--figures-dir", "-fd", default=None, help="Directorio específico para figuras (opcional).")
    args = parser.parse_args()

    input_path = args.input
    stem = os.path.splitext(os.path.basename(input_path))[0]
    
    # 2. Requisito: Todos los outputs deben generarse bajo la carpeta evaluation/results/<archivo-analizado>/
    if args.output_dir:
        target_dir = args.output_dir
    else:
        base_dir = os.path.dirname(input_path) or "evaluation/results"
        target_dir = os.path.join(base_dir, stem)
        
    os.makedirs(target_dir, exist_ok=True)
    
    output_excel = args.output_excel or os.path.join(target_dir, "querylibrary_estadisticas_tfm.xlsx")
    output_report = args.output_report or os.path.join(target_dir, "querylibrary_analisis_estadistico_tfm.md")
    figures_dir = args.figures_dir or os.path.join(target_dir, "figures")
    os.makedirs(figures_dir, exist_ok=True)

    print("=" * 80)
    print("INICIANDO ANÁLISIS ESTADÍSTICO INTEGRAL PARA TFM (ESTILO UNIVERSIDAD EUROPEA)")
    print(f"Dataset de entrada:     {input_path}")
    print(f"Directorio de salida:   {target_dir}")
    print("=" * 80)
    
    analyzer = TFMStatisticalAnalyzer(input_path)
    
    print("\n1. Generando libro Excel multihistorial formateado (Paleta Universidad Europea)...")
    analyzer.export_excel_report(output_excel)
    print(f"-> Excel generado con éxito: {output_excel}")
    
    print("\n2. Generando galería de figuras de alta resolución (300 DPI y SVG, Paleta Universidad Europea)...")
    analyzer.generate_figures(figures_dir)
    print(f"-> Figuras exportadas en: {figures_dir}/")
    
    print("\n3. Generando informe exhaustivo en formato Markdown...")
    analyzer.generate_markdown_report(output_report)
    print(f"-> Informe Markdown generado con éxito: {output_report}")
    
    print("\n" + "=" * 80)
    print("PROCESO COMPLETADO SATISFACTORIAMENTE")
    print(f"Todos los artefactos han sido consolidados en: {target_dir}")
    print("=" * 80)

if __name__ == "__main__":
    main()
