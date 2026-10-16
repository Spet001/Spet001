import os
import re
import requests
import json
import urllib.parse

GITHUB_USERNAME = "Spet001"
GITLAB_USERNAME = "Spet001"
ITCHIO_TOKEN = os.environ.get("ITCHIO_TOKEN")
NEXUSMODS_TOKEN = os.environ.get("NEXUSMODS_TOKEN")

# Nexus Mods lista de mods principais: (nome_do_jogo_na_url, id_do_mod)
NEXUS_MODS = [
    ("finalfantasy13", 59),
    ("likeadragonpirateyakuzainhawaii", 181)
]

def get_github_recent_projects():
    print("Buscando repositorios recentes do GitHub...")
    projects = []
    url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    # Se houver GITHUB_TOKEN no ambiente, usamos para aumentar rate limit
    gh_token = os.environ.get("GITHUB_TOKEN")
    if gh_token:
        headers["Authorization"] = f"token {gh_token}"
        
    response = requests.get(url, headers=headers, params={"sort": "pushed", "direction": "desc", "per_page": 10})
    if response.status_code == 200:
        repos = response.json()
        count = 0
        for repo in repos:
            # Pula forks se quiser apenas projetos autorais, ou conta os 3 primeiros
            name = repo.get("name")
            # Ignora o proprio repo de profile se desejar, ou inclui
            if name == GITHUB_USERNAME:
                continue
            
            repo_url = repo.get("html_url")
            desc = repo.get("description") or "Sem descrição."
            lang = repo.get("language")
            badge = ""
            if lang:
                safe_lang = lang.replace("-", "--").replace("_", "__")
                safe_lang = urllib.parse.quote(safe_lang)
                badge = f"![{lang}](https://img.shields.io/badge/{safe_lang}-232F3E?style=flat-square) "
                
            projects.append(f"- [**{name}**]({repo_url}) {badge}- {desc}")
            count += 1
            if count >= 3:
                break
    else:
        print(f"Erro ao buscar GitHub: {response.status_code}")
    return projects

def get_gitlab_projects():
    print("Buscando projetos do GitLab...")
    projects = []
    url = f"https://gitlab.com/api/v4/users/{GITLAB_USERNAME}/projects"
    response = requests.get(url, params={"visibility": "public", "per_page": 50})
    if response.status_code == 200:
        data = response.json()
        for proj in data:
            name = proj.get("name")
            url = proj.get("web_url")
            desc = proj.get("description", "Sem descrição.")
            if not desc: desc = "Sem descrição."
            
            proj_id = proj.get("id")
            lang_url = f"https://gitlab.com/api/v4/projects/{proj_id}/languages"
            lang_res = requests.get(lang_url)
            badges = ""
            if lang_res.status_code == 200:
                langs = lang_res.json()
                for lang in list(langs.keys())[:3]:
                    safe_lang = lang.replace("-", "--").replace("_", "__")
                    safe_lang = urllib.parse.quote(safe_lang)
                    badges += f"![{lang}](https://img.shields.io/badge/{safe_lang}-232F3E?style=flat-square) "
            
            projects.append(f"- [**{name}**]({url}) {badges}- {desc}")
    else:
        print(f"Erro ao buscar GitLab: {response.status_code}")
    return projects

def get_itchio_projects():
    print("Buscando projetos da itch.io...")
    projects = []
    if not ITCHIO_TOKEN:
        print("ITCHIO_TOKEN não encontrado. Pulando...")
        return projects
    
    url = "https://itch.io/api/1/key/my-games"
    response = requests.get(url, headers={"Authorization": f"Bearer {ITCHIO_TOKEN}"})
    if response.status_code == 200:
        data = response.json()
        for game in data.get("games", []):
            name = game.get("title")
            url = game.get("url")
            desc = game.get("short_text", "Sem descrição.")
            projects.append(f"- [**{name}**]({url}) - {desc}")
    else:
        print(f"Erro ao buscar itch.io: {response.status_code}")
    return projects

def get_nexus_mods():
    print("Buscando dados do Nexus Mods...")
    projects = []
    if not NEXUSMODS_TOKEN:
        print("NEXUSMODS_TOKEN não encontrado. Pulando...")
        return projects
    
    headers = {
        "apikey": NEXUSMODS_TOKEN,
        "accept": "application/json"
    }
    
    for game_domain, mod_id in NEXUS_MODS:
        url = f"https://api.nexusmods.com/v1/games/{game_domain}/mods/{mod_id}.json"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            name = data.get("name")
            mod_url = f"https://www.nexusmods.com/{game_domain}/mods/{mod_id}"
            desc = data.get("summary", "Sem descrição.")
            downloads = data.get("mod_downloads", 0)
            projects.append(f"- [**{name}**]({mod_url}) - {desc} *(↓ {downloads} Downloads)*")
        else:
             print(f"Erro ao buscar mod {mod_id} ({game_domain}): {response.status_code}")
    return projects

def generate_markdown(github_data, gitlab_data, itch_data, nexus_data):
    md = "### GitHub (Commits Recentes)\n"
    if github_data:
        md += "\n".join(github_data) + "\n\n"
    else:
        md += "_Nenhum repositório recente encontrado._\n\n"

    md += "### GitLab\n"
    if gitlab_data:
        md += "\n".join(gitlab_data) + "\n\n"
    else:
        md += "_Nenhum projeto encontrado._\n\n"
        
    md += "### itch.io\n"
    if itch_data:
        md += "\n".join(itch_data) + "\n\n"
    else:
        md += "_Nenhum projeto encontrado._\n\n"
        
    md += "### Nexus Mods\n"
    if nexus_data:
        md += "\n".join(nexus_data) + "\n\n"
    else:
        md += "_Nenhum projeto encontrado._\n\n"
        
    return md

def update_readme(new_content):
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            readme = f.read()
            
        marker_start = "<!-- START_PROJETOS -->"
        marker_end = "<!-- END_PROJETOS -->"
        
        if marker_start not in readme or marker_end not in readme:
            print("Marcadores não encontrados no README.md!")
            return

        pattern = f"{marker_start}.*?{marker_end}"
        replacement = f"{marker_start}\n{new_content}\n{marker_end}"
        
        new_readme = re.sub(pattern, replacement, readme, flags=re.DOTALL)
        
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(new_readme)
        print("README.md atualizado com sucesso!")
    except FileNotFoundError:
        print("README.md não encontrado no diretório atual.")

if __name__ == "__main__":
    github_projects = get_github_recent_projects()
    gitlab_projects = get_gitlab_projects()
    itch_projects = get_itchio_projects()
    nexus_projects = get_nexus_mods()
    
    new_markdown = generate_markdown(github_projects, gitlab_projects, itch_projects, nexus_projects)
    update_readme(new_markdown)
