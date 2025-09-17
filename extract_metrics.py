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


def processar_ck_results_repo(repo_name, results_dir, pasta_saida):
    """Processa resultados CK de um repositório específico dos arquivos únicos sobrescritos"""
    
    # Procurar arquivo class CSV no diretório principal
    class_files = list(results_dir.glob("*class*.csv"))
    if not class_files:
        print(f"Nenhum arquivo class CSV encontrado em {results_dir}")
        return []
    
    class_file = class_files[0]
    print(f"Processando métricas de {repo_name}")
    
    try:
        class_csv = pd.read_csv(class_file)
        if class_csv.empty:
            return []
        
        metricas_repo = []
        for _, row in class_csv.iterrows():
            caminho_arquivo = row.get("file", "")
            loc = int(row.get("loc", 0)) if pd.notnull(row.get("loc", 0)) else 0
            cbo = int(row.get("cbo", 0)) if pd.notnull(row.get("cbo", 0)) else 0
            dit = int(row.get("dit", 0)) if pd.notnull(row.get("dit", 0)) else 0
            lcom = int(row.get("lcom", 0)) if pd.notnull(row.get("lcom", 0)) else 0

            if caminho_arquivo:
                caminho_java = Path(caminho_arquivo)
                linhas_comentario = contar_linhas_comentarios(caminho_java)
                
                metricas_repo.append({
                    "repositorio": repo_name,
                    "arquivo": caminho_java.name,
                    "loc": loc,
                    "comentarios": linhas_comentario,
                    "cbo": cbo,
                    "dit": dit,
                    "lcom": lcom
                })
        
        if metricas_repo:
            df_repo = pd.DataFrame(metricas_repo)
            totais_repo = {
                "repositorio": repo_name,
                "loc_total": df_repo["loc"].sum(),
                "comentarios_total": df_repo["comentarios"].sum(),
                "cbo_total": df_repo["cbo"].sum(),
                "dit_total": df_repo["dit"].sum(),
                "lcom_total": df_repo["lcom"].sum(),
                "arquivos_java": len(metricas_repo),
                "loc_media_por_arquivo": round(df_repo["loc"].mean(), 2),
                "comentarios_media_por_arquivo": round(df_repo["comentarios"].mean(), 2)
            }
            
            arquivo_per_repo = pasta_saida / "total_metrics_per_repo.csv"
            df_novo_repo = pd.DataFrame([totais_repo])
            
            if arquivo_per_repo.exists():
                df_existente = pd.read_csv(arquivo_per_repo)
                df_combined = pd.concat([df_existente, df_novo_repo], ignore_index=True)
            else:
                df_combined = df_novo_repo
            
            df_combined.to_csv(arquivo_per_repo, index=False)
            df_combined.to_excel(pasta_saida / "total_metrics_per_repo.xlsx", index=False)
            
            print(f"Métricas de {repo_name} adicionadas ao total_metrics_per_repo")
            print(f"   Arquivos: {len(metricas_repo)}")
            print(f"   LOC Total: {totais_repo['loc_total']:,}")
            print(f"   Comentários: {totais_repo['comentarios_total']:,}")
            
        return metricas_repo
        
    except Exception as e:
        print(f"Erro ao processar métricas de {repo_name}: {e}")
        return []


def gerar_metrics_totais_finais(pasta_saida):
    """Gera métricas totais finais baseadas no total_metrics_per_repo"""
    arquivo_per_repo = pasta_saida / "total_metrics_per_repo.csv"
    
    if not arquivo_per_repo.exists():
        print("Arquivo total_metrics_per_repo.csv não encontrado")
        return None
        
    df_per_repo = pd.read_csv(arquivo_per_repo)
    
    totais_finais = {
        "loc_total": df_per_repo["loc_total"].sum(),
        "comentarios_total": df_per_repo["comentarios_total"].sum(),
        "cbo_total": df_per_repo["cbo_total"].sum(),
        "dit_total": df_per_repo["dit_total"].sum(),
        "lcom_total": df_per_repo["lcom_total"].sum(),
        "repositorios_total": len(df_per_repo),
        "arquivos_java_total": df_per_repo["arquivos_java"].sum()
    }
    
    df_totais_finais = pd.DataFrame([totais_finais])
    df_totais_finais.to_csv(pasta_saida / "total_metrics.csv", index=False)
    df_totais_finais.to_excel(pasta_saida / "total_metrics.xlsx", index=False)
    print("Métricas totais finais salvas")
    
    df_per_repo_sorted = df_per_repo.sort_values("loc_total", ascending=False)
    df_per_repo_sorted.to_csv(arquivo_per_repo, index=False)
    df_per_repo_sorted.to_excel(pasta_saida / "total_metrics_per_repo.xlsx", index=False)
    
    return df_per_repo_sorted


def exibir_resumo_final(df_per_repo_sorted):
    """Exibe resumo final das métricas por repositório"""
    if df_per_repo_sorted is None or df_per_repo_sorted.empty:
        print("Nenhum dado para exibir")
        return
        
    print(f"\n RESUMO FINAL:")
    print("="*70)
    for _, row in df_per_repo_sorted.iterrows():
        print(f" {row['repositorio']}")
        print(f"   Arquivos: {int(row['arquivos_java'])}")
        print(f"   LOC Total: {int(row['loc_total']):,}")
        print(f"   Comentários: {int(row['comentarios_total']):,}")
        print(f"   LOC/arquivo: {row['loc_media_por_arquivo']}")
        print()
