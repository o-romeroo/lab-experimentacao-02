import requests
from dotenv import load_dotenv
from datetime import datetime, timezone
import pandas as pd
import time
from pathlib import Path
import subprocess
import os


load_dotenv()

token = os.getenv("GITHUB_TOKEN")

# Project-relative paths with environment-variable overrides for portability
BASE_DIR = Path(__file__).resolve().parent
CK_JAR = Path(os.getenv("CK_JAR", BASE_DIR / "ck" / "target" / "ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar"))
REPOSITORIES_DIR = Path(os.getenv("REPOSITORIES_DIR", BASE_DIR / "repositories"))
RESULTS_DIR = Path(os.getenv("RESULTS_DIR", BASE_DIR / "results"))
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))

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
        # filtro de linguagem Java
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
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / "repository_data.xlsx"
    df.to_excel(out_path, index=False)
    
def run_ck_on_repo(repo_name):
    repo_dir = REPOSITORIES_DIR / repo_name
    out_dir = RESULTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    if not CK_JAR.exists():
        raise FileNotFoundError(f"CK jar not found at {CK_JAR}. Set CK_JAR environment variable to the jar location.")

    cmd = [
        "java", "-Xmx4g", "-jar", str(CK_JAR),
        str(repo_dir),
        "true",
        "true",
        str(out_dir)
    ]

    subprocess.check_call(cmd, cwd=str(repo_dir.parent))
    

def clone_repository(url: str, destino: Path):
    """
    Clona o repositório Git a partir da URL na pasta de destino especificada.

    Parâmetros:
    - url (str): URL HTTPS do repositório no GitHub.
    - destino (Path): Caminho para a pasta onde o repositório será clonado.
    """
    repo_name = url.rstrip("/").split("/")[-1]
    repo_path = destino / repo_name

    if repo_path.exists():
        print(f"Repositório '{repo_name}' já existe em {repo_path}, pulando clone.")
        return

    destino.mkdir(parents=True, exist_ok=True)

    print(f"Clonando {url} em {repo_path} ...")
    subprocess.run(["git", "clone", url, str(repo_path)], check=True)
    print(f"Repositório clonado: {repo_path}")




if __name__ == "__main__":
    try:
        if token is None:
            print("Warning: GITHUB_TOKEN not set. You may hit API rate limits.")

        popular_repos = get_popular_repositories_java(1000)
        collect_and_save_repo_info(popular_repos)

        destino = REPOSITORIES_DIR

        for repo in popular_repos:
            repo_url = get_repository_url(repo)
            if repo_url:
                clone_repository(repo_url, destino)
                run_ck_on_repo(repo["name"])
            else:
                print(f"Skipping repo with no URL: {repo}")
    except Exception as e:
        print(f"Error fetching popular repositories: {e}")
