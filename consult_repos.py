import requests
from dotenv import load_dotenv
from datetime import datetime, timezone
import pandas as pd
import time
from pathlib import Path
import subprocess
import os
import shutil
from extract_metrics import processar_ck_results_repo, gerar_metrics_totais_finais, exibir_resumo_final
import stat
import tempfile
import os

def remove_readonly(func, path, _):
    """Remove sinalizador de somente leitura e tenta excluir novamente (para arquivos Git do Windows)"""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def safe_remove_repository(repo_path):
    """Remove repositório de forma segura, lidando com arquivos somente leitura"""
    try:
        shutil.rmtree(repo_path, onerror=remove_readonly)
        print(f"Repositório {repo_path.name} removido para liberar espaço")
        return True
    except Exception as clean_error:
        print(f"AVISO: Erro ao remover {repo_path.name}: {clean_error}")
        
        try:
            for root, dirs, files in os.walk(repo_path):
                for dir in dirs:
                    os.chmod(os.path.join(root, dir), stat.S_IWRITE)
                for file in files:
                    os.chmod(os.path.join(root, file), stat.S_IWRITE)
            shutil.rmtree(repo_path, ignore_errors=True)
            print(f"Repositório {repo_path.name} removido com força bruta")
            return True
        except:
            pass
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                result = subprocess.run([
                    'robocopy', temp_dir, str(repo_path), '/MIR', '/NFL', '/NDL', '/NJS'
                ], capture_output=True, text=True)
                if result.returncode < 8:
                    os.rmdir(repo_path)
                    print(f"Repositório {repo_path.name} removido via robocopy")
                    return True
        except Exception as e:
            print(f"AVISO: Robocopy também falhou: {e}")
        
        print(f"ERRO: Não foi possível remover {repo_path.name} - continuando...")
        return False

load_dotenv()

token = os.getenv("GITHUB_TOKEN")
path_repositories = os.getenv("PATH_REPOSITORIES")  # e.g., r"C:\path\to\repositories"
path_ck_jar = os.getenv("PATH_CK_JAR")  # e.g., r"C:\path\to\ck.jar"
path_output_ck = os.getenv("PATH_OUTPUT_CK")  # e.g., r"C:\path\to\output"
path_results_metrics = os.getenv("PATH_RESULTS_METRICS")  # e.g., r"C:\path\to\results"
java_path = os.getenv("JAVA_PATH")  # e.g., r"C:\Program Files\Java\jdk-24\bin\java.exe"

def get_popular_repositories_java(num_repos):
    """
    Retorna os repositórios Java mais populares do GitHub, ordenados por número de estrelas.

    Parâmetros:
    - num_repos (int): número máximo de repositórios a buscar (até 1000).

    Retorna:
    - list: lista de dicionários, cada um representando um repositório conforme o campo "items" da resposta da API.

    Arremessa:
    - Exception: se alguma requisição HTTP não retornar status 200.

    Observações:
    - A função faz a paginação automaticamente para buscar mais de 100 repositórios, respeitando o limite de 1000 imposto pela API do GitHub.
    - Insere um delay de 2 segundos entre as requisições para evitar atingir o rate limit da API.
    """
    all_repos = []
    per_page = 100
    for page in range(1, (num_repos // per_page) + 2):
        url = (
            f"https://api.github.com/search/repositories"
            f"?q=language:Java+stars:>0&sort=stars&order=desc"
            f"&per_page={per_page}&page={page}"
        )
        headers = {"Authorization": f"Token {token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            items = response.json()["items"]
            all_repos.extend(items)
            if len(all_repos) >= num_repos or not items:
                break
        else:
            raise Exception(
                f"Error fetching repositories: {response.status_code} - {response.text}"
            )
        time.sleep(2)  
    return all_repos[:num_repos]

    
def get_repository_age_years(repo_details):
    """Calcula a idade do repositório em anos.

    Parâmetros:
    - repo_details (dict): dicionário com os detalhes do repositório (deve conter a chave "created_at").

    Retorna:
    - float: idade em anos (aproximação usando 365.25 dias por ano).
    """
    created_at = repo_details["created_at"]
    created_at_dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    age_years = (now - created_at_dt).days / 365.25
    return age_years
    

def get_repositories_details(owner, repository):
    """Busca os detalhes de um repositório pelo endpoint da API do GitHub.

    Parâmetros:
    - owner (str): proprietário/organização do repositório.
    - repository (str): nome do repositório.

    Retorna:
    - dict: JSON convertido para dicionário com os detalhes do repositório.

    Arremessa:
    - Exception: se a requisição HTTP não retornar status 200.
    """
    url = f"https://api.github.com/repos/{owner}/{repository}"
    headers = {
        "Authorization": f"Token {token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching repository details: {response.status_code} - {response.text}")

def get_repository_releases_count(owner, repository):
    """Conta o número total de releases de um repositório paginando o endpoint de releases.

    Parâmetros:
    - owner (str): proprietário/organização do repositório.
    - repository (str): nome do repositório.

    Retorna:
    - int: número total de releases, após realizar a soma destas informações contidas em todas as páginas.

    Arremessa:
    - Exception: se alguma requisição HTTP de página retornar status diferente de 200.
    """
    url = f"https://api.github.com/repos/{owner}/{repository}/releases"
    headers = {"Authorization": f"Token {token}"}
    page = 1
    releases = []
    while True:
        print(f"Fetching releases for page {page}")
        response = requests.get(f"{url}?page={page}&per_page=100", headers=headers)
        if response.status_code == 200:
            page_releases = response.json()
            if not page_releases:
                break
            releases.extend(page_releases)
            page += 1
        else:
            raise Exception(f"Error fetching repository releases: {response.status_code} - {response.text}")
    return len(releases)
    
    
def get_repository_url(repo_details):
    """Retorna a URL pública do repositório no GitHub."""
    return repo_details.get("html_url")

def get_stargazers_count(repo_details):
    """Retorna a quantidade de estrelas (stargazers) do repositório."""
    return repo_details.get("stargazers_count", 0)


def collect_and_save_repo_info(repos):
    """Coleta informações detalhadas de uma lista de repositórios e salva em um arquivo Excel.

    Parâmetros:
    - repos (list): lista de dicionários com informações dos repositórios; cada dicionário deve conter as chaves "full_name", "name" e "owner".

    Retorna:
    - None: função salva os dados em "repository_data.xlsx" e não retorna valor.

    Arremessa:
    - Exception: se alguma chamada à API feita durante a coleta falhar (propaga exceções das funções chamadoras).

    Observações:
    - Faz chamadas adicionais à API para cada repositório; insere um delay de 3 segundos entre requisições para suavizar a carga na API e não tomar timeout por excesso de requisições feitas em menos de 1 minuto.
    """
    rows = []

    for index, repo in enumerate(repos):
        print(f"Processing repository: {repo['full_name']}\nTotal remaining: {len(repos) - index - 1}")
        owner = repo["owner"]["login"]
        repo_name = repo["name"]

        repo_details = get_repositories_details(owner, repo_name)
        url = get_repository_url(repo_details)
        stars_count = get_stargazers_count(repo_details)
        releases_count = get_repository_releases_count(owner, repo_name)
        repo_age = round(get_repository_age_years(repo_details), 2)

        rows.append({
            "full_name": repo["full_name"],
            "repo_name": repo_name,
            "url": url,
            "stars_count": stars_count,
            "releases_count": releases_count,
            "repo_age_years": repo_age,
        })
        time.sleep(3)
    df = pd.DataFrame(rows)
    df.to_excel("data/repository_data.xlsx", index=False)
    
def run_ck_on_repo(jar_path, repo_dir, out_dir):
    """Executa CK em um repositório específico"""
    
    out_dir.mkdir(parents=True, exist_ok=True)
    
    java_files = list(repo_dir.rglob("*.java"))
    if not java_files:
        print(f"AVISO: Nenhum arquivo .java encontrado em: {repo_dir.name}")
        return False

    print(f"Executando CK em {repo_dir.name} ({len(java_files)} arquivos Java)")
    original_cwd = os.getcwd()
    
    cmd = [
        java_path, "-Xmx4g", "-jar", str(jar_path),
        str(repo_dir),
        "true",  
        "0",
        "true"
    ]
    
    try:
        os.chdir(str(out_dir))
        subprocess.check_call(cmd)
        print(f"Análise CK concluída para {repo_dir.name}")
        
        csv_files = list(out_dir.glob("*.csv"))
        if csv_files:
            print(f"Arquivos gerados: {len(csv_files)} CSVs")
            return True
        else:
            print(f"AVISO: Nenhum arquivo CSV foi gerado para {repo_dir.name}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"ERRO: Erro ao analisar {repo_dir.name}: {e}")
        return False
    finally:
        os.chdir(original_cwd)
    

def clone_repository(url: str, destino: Path):
    """
    Clona o repositório Git usando shallow clone para otimizar velocidade e espaço.
    
    Usa --depth 1 --single-branch para baixar apenas o último commit da branch padrão.

    Parâmetros:
    - url (str): URL HTTPS do repositório no GitHub.
    - destino (Path): Caminho para a pasta onde o repositório será clonado.
    """
    repo_name = url.rstrip("/").split("/")[-1]
    repo_path = destino / repo_name

    if repo_path.exists():
        print(f"Repositório '{repo_name}' já existe, pulando clone.")
        return

    destino.mkdir(parents=True, exist_ok=True)

    print(f"Clonando {repo_name} (shallow clone)...")
    try:
        # Shallow clone otimizado - apenas último commit da branch padrão
        subprocess.run([
            "git", "clone", 
            "--depth", "1",           # Apenas último commit
            "--single-branch",        # Apenas branch padrão  
            url, 
            str(repo_path)
        ], check=True, capture_output=True, text=True)
        print(f"Repositório clonado: {repo_name}")
        
    except subprocess.CalledProcessError as e:
        print(f"ERRO: Erro ao clonar {repo_name}: {e.stderr}")
        try:
            print(f"Tentando clone tradicional para {repo_name}...")
            subprocess.run(["git", "clone", url, str(repo_path)], check=True)
            print(f"Clone tradicional bem-sucedido: {repo_name}")
        except subprocess.CalledProcessError as e2:
            print(f"ERRO: Clone tradicional também falhou para {repo_name}: {e2}")
            raise


def main():
    """Função principal que executa o pipeline completo de análise de repositórios Java.

    Executa as seguintes etapas:
    1. Busca os repositórios Java mais populares do GitHub
    2. Coleta e salva informações detalhadas dos repositórios em Excel
    3. Clona cada repositório usando shallow clone para otimização
    4. Executa análise CK (Code Quality) em cada repositório
    5. Processa e agrega as métricas de qualidade
    6. Remove repositórios após processamento para economizar espaço
    7. Gera relatórios finais consolidados

    Parâmetros:
    - Nenhum: utiliza variáveis de ambiente configuradas no arquivo .env

    Retorna:
    - None: função executa o pipeline e salva resultados em arquivos CSV/Excel

    Arremessa:
    - Exception: se ocorrer erro geral no processamento (capturado e logado)

    Observações:
    - Processa até 1000 repositórios Java mais populares do GitHub
    - Usa shallow clone (--depth 1) para otimizar velocidade e espaço em disco  
    - Implementa tratamento robusto de erros com continuação do processamento
    - Remove repositórios após cada análise para economizar espaço em disco
    - Gera estatísticas finais de sucessos e falhas
    """
    try:
        popular_repos = get_popular_repositories_java(1000)  
        collect_and_save_repo_info(popular_repos)
        
        destino = path_repositories
        destino.mkdir(parents=True, exist_ok=True)

        ck_jar = path_ck_jar
        out_dir = path_output_ck
        out_dir.mkdir(parents=True, exist_ok=True)

        pasta_saida = path_results_metrics
        pasta_saida.mkdir(parents=True, exist_ok=True)
        
        arquivo_per_repo = pasta_saida / "total_metrics_per_repo.csv"
        if arquivo_per_repo.exists():
            arquivo_per_repo.unlink()
        arquivo_per_repo_xlsx = pasta_saida / "total_metrics_per_repo.xlsx"  
        if arquivo_per_repo_xlsx.exists():
            arquivo_per_repo_xlsx.unlink()
        
        print(f"\n{'='*50}")
        print("Iniciando análise CK dos repositórios...")
        print(f"{'='*50}")
        
        successful_analyses = 0
        failed_analyses = 0
        
        for i, repo in enumerate(popular_repos, 1):
            repo_name = repo["name"]
            repo_path = destino / repo_name
            print(f"\nProcessando {i}/{len(popular_repos)}: {repo_name}")
            
            try:
                clone_repository(get_repository_url(repo), destino)
                
                if repo_path.exists():
                    ck_success = run_ck_on_repo(ck_jar, repo_path, out_dir)
                    
                    if ck_success:
                        processar_ck_results_repo(repo_name, out_dir, pasta_saida)
                        successful_analyses += 1
                        print(f"Repositório {repo_name} processado e adicionado ao total")
                    else:
                        failed_analyses += 1
                        print(f"ERRO: Falha ao processar {repo_name}")
                        
                    safe_remove_repository(repo_path)
                        
                else:
                    print(f"AVISO: Repositório não encontrado: {repo_path}")
                    failed_analyses += 1
                    
            except Exception as e:
                print(f"ERRO: Erro ao processar {repo_name}: {e}")
                print(f"Pulando {repo_name} e continuando com próximo repositório...")
                failed_analyses += 1
                
                if repo_path.exists():
                    safe_remove_repository(repo_path)
                continue
        
        print(f"\n{'='*50}")
        print("Gerando métricas totais finais...")
        print(f"{'='*50}")
        
        df_per_repo_sorted = gerar_metrics_totais_finais(pasta_saida)
        if df_per_repo_sorted is not None:
            exibir_resumo_final(df_per_repo_sorted)
        
        print(f"\n{'='*50}")
        print("Processamento COMPLETO!")
        print(f"Análises bem-sucedidas: {successful_analyses}")
        print(f"ERRO: Falhas na análise: {failed_analyses}")
        print(f"Resultados CK salvos em: {out_dir}")
        print(f"Métricas salvas em: {pasta_saida}")
        print(f"{'='*50}")
        
    except Exception as e:
        print(f"ERRO: Erro geral: {e}")


if __name__ == "__main__":
    main()
