import pandas as pd
from pathlib import Path

def contar_linhas_comentarios(caminho_java):
    """Conta linhas de comentário em um arquivo .java"""
    total_comentarios = 0
    try:
        with open(caminho_java, "r", encoding="utf-8") as f:
            in_block_comment = False
            for linha in f:
                linha = linha.strip()
                if in_block_comment:
                    total_comentarios += 1
                    if "*/" in linha:
                        in_block_comment = False
                elif linha.startswith("//"):
                    total_comentarios += 1
                elif "/*" in linha:
                    total_comentarios += 1
                    if "*/" not in linha:
                        in_block_comment = True
    except Exception:
        pass  
    return total_comentarios

def processar_ck_results():
    pasta_ck = Path(r"C:\Users\Lucas\Desktop\lab-experimentacao-02\results_ck")
    pasta_saida = Path(r"C:\Users\Lucas\Desktop\lab-experimentacao-02\results_metrics")
    pasta_saida.mkdir(parents=True, exist_ok=True)

    class_csv = None
    for arquivo in pasta_ck.glob("*class*.csv"):
        class_csv = pd.read_csv(arquivo)
        break

    if class_csv is None or class_csv.empty:
        return

    metricas = []

    for _, row in class_csv.iterrows():
        caminho_arquivo = row.get("file", "")
        loc = row.get("loc", 0)
        cbo = row.get("cbo", 0)
        dit = row.get("dit", 0)
        lcom = row.get("lcom", 0)

        loc = int(loc) if pd.notnull(loc) else 0
        cbo = int(cbo) if pd.notnull(cbo) else 0
        dit = int(dit) if pd.notnull(dit) else 0
        lcom = int(lcom) if pd.notnull(lcom) else 0

        caminho_java = Path(caminho_arquivo)
        linhas_comentario = contar_linhas_comentarios(caminho_java)

        metricas.append({
            "arquivo": caminho_java.name,
            "loc": loc,
            "comentarios": linhas_comentario,
            "cbo": cbo,
            "dit": dit,
            "lcom": lcom
        })

    df_metricas = pd.DataFrame(metricas)

    df_metricas.to_csv(pasta_saida / "file_metrics.csv", index=False)
    df_metricas.to_excel(pasta_saida / "file_metrics.xlsx", index=False)

    totais = {
        "loc_total": df_metricas["loc"].sum(),
        "comentarios_total": df_metricas["comentarios"].sum(),
        "cbo_total": df_metricas["cbo"].sum(),
        "dit_total": df_metricas["dit"].sum(),
        "lcom_total": df_metricas["lcom"].sum()
    }
    df_totais = pd.DataFrame([totais])
    df_totais.to_csv(pasta_saida / "total_metrics.csv", index=False)
    df_totais.to_excel(pasta_saida / "total_metrics.xlsx", index=False)


processar_ck_results()
