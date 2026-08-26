import os
import re
import requests
import json
import urllib.parse

GITLAB_USERNAME = "Spet001"
ITCHIO_TOKEN = os.environ.get("ITCHIO_TOKEN")
NEXUSMODS_TOKEN = os.environ.get("NEXUSMODS_TOKEN")

# Nexus Mods não possui um endpoint público que retorne "todos os mods que eu criei" de forma simples.
# Por isso, definimos uma lista dos seus mods principais: (nome_do_jogo_na_url, id_do_mod)
NEXUS_MODS = [
    ("finalfantasy13", 59),
    ("likeadragonpirateyakuzainhawaii", 181)
]

def get_gitlab_projects():
    print("Buscando projetos do GitLab...")
    projects = []
    url = f"https://gitlab.com/api/v4/users/{GITLAB_USERNAME}/projects"
    # Buscamos os projetos públicos (per_page 50 deve ser suficiente para o perfil)
    response = requests.get(url, params={"visibility": "public", "per_page": 50})
    if response.status_code == 200:
        data = response.json()
        for proj in data:
            name = proj.get("name")
            url = proj.get("web_url")
            desc = proj.get("description", "Sem descrição.")
            if not desc: desc = "Sem descrição."
            
            # Busca as linguagens usadas no projeto para gerar as Badges dinamicamente
            proj_id = proj.get("id")
            lang_url = f"https://gitlab.com/api/v4/projects/{proj_id}/languages"
            lang_res = requests.get(lang_url)
            badges = ""
            if lang_res.status_code == 200:
                langs = lang_res.json()
                for lang in list(langs.keys())[:3]: # Pegamos o Top 3 linguagens para não poluir
                    # Adiciona uma badge simples para cada linguagem
                    safe_lang = lang.replace("-", "--").replace("_", "__")
                    safe_lang = urllib.parse.quote(safe_lang)
                    badges += f"![{lang}](https://img.shields.io/badge/{safe_lang}-232F3E?style=flat-square) "
            
            projects.append(f"- 🦊 [**{name}**]({url}) {badges}- {desc}")
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
            projects.append(f"- 🎮 [**{name}**]({url}) - {desc}")
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
            projects.append(f"- ⚔️ [**{name}**]({mod_url}) - {desc} *(↓ {downloads} Downloads)*")
        else:
             print(f"Erro ao buscar mod {mod_id} ({game_domain}): {response.status_code}")
    return projects

def generate_markdown(gitlab_data, itch_data, nexus_data):
    md = "### 🦊 GitLab\n"
    if gitlab_data:
        md += "\n".join(gitlab_data) + "\n\n"
    else:
        md += "_Nenhum projeto encontrado._\n\n"
        
    md += "### 🎮 itch.io\n"
    if itch_data:
        md += "\n".join(itch_data) + "\n\n"
    else:
        md += "_Nenhum projeto encontrado._\n\n"
        
    md += "### ⚔️ Nexus Mods\n"
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
    gitlab_projects = get_gitlab_projects()
    itch_projects = get_itchio_projects()
    nexus_projects = get_nexus_mods()
    
    new_markdown = generate_markdown(gitlab_projects, itch_projects, nexus_projects)
    update_readme(new_markdown)
