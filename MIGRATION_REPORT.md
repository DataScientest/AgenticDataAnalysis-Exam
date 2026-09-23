# Rapport de migration : POC de l'examen sur LangChain 1.x / LangGraph 1.x

Repo : `DataScientest/AgenticDataAnalysis-Exam`, branche `feature/no-ref/langchain-v1-poc-compat`, vers `main`.
Date : 2026-09-23. **Énoncé (`README.md`) et barème inchangés.**

## Pourquoi

La Phase 1 de l'énoncé demande de lancer le POC. Avec les dépendances non épinglées, il ne s'installait plus et ne démarrait plus :

- `Pages/graph/nodes.py` importait `ToolInvocation, ToolExecutor` depuis `langgraph.prebuilt`, supprimés en LangGraph 1.x ;
- `requirements.txt` listait `sklearn`, paquet PyPI factice qui échoue volontairement à l'installation (il faut `scikit-learn`) ;
- `langchain_experimental` était importé sans être déclaré, et ce paquet est aujourd'hui en fin de vie ;
- `requirements-test.txt` exigeait `pytest-security`, qui n'existe pas sur PyPI (404), si bien que la commande de l'énoncé `pip install -r requirements-test.txt` échouait ;
- `backend/tests/test_api.py` contenait une erreur de syntaxe (`TODO: Implement ...` hors commentaire), qui faisait échouer la collecte de `pytest backend/tests/`.

Correction **minimale** : les 5 failles que l'examen demande de trouver et corriger restent intactes (historique en mémoire, aucune auth, visualisations non persistées, Streamlit monolithique, `exec()` brut dans `complete_python_task`).

## Versions

| Paquet | Avant | Après |
|---|---|---|
| langchain | non épinglé (`requirements-test`: `>=0.1`) | 1.3.9 |
| langchain-core | non épinglé (`>=0.1`) | 1.4.7 |
| langgraph | non épinglé | 1.2.5 |
| langchain-openai | non épinglé (`>=0.1`) | 1.3.2 |
| langchain-experimental | importé, non déclaré | retiré (import inutilisé) |
| sklearn / scikit-learn | `sklearn` (non installable) | scikit-learn 1.9.1 |
| pandas / streamlit / plotly | non épinglés | 3.0.6 / 1.64.0 / 7.1.0 |

Même pile LangChain que le repo de pratique `AI-Agents-MLOps-Course`. Les dépendances de test non-LangChain de `requirements-test.txt` n'ont pas été modifiées.

## Fichiers modifiés

- `Pages/graph/nodes.py` : `ToolExecutor.batch(ToolInvocation(...), return_exceptions=True)` devient un appel direct `tools_by_name[name].invoke({**args, "graph_state": state})`, avec capture des exceptions (même sémantique ; la boucle agent vers outils, le retour `(message, state_updates)` et l'`InjectedState` sont inchangés). LLM `ChatOpenAI(model="gpt-4o")` rendu configurable pour toute API compatible OpenAI : `LLM_MODEL` (par défaut `openai/gpt-oss-120b`), `LLM_API_BASE` (par défaut Groq), `LLM_API_KEY`.
- `Pages/graph/tools.py` : suppression de `from langchain_experimental.utilities import PythonREPL` et de `repl = PythonREPL()`, jamais utilisés. Le `exec()` brut est conservé.
- `requirements.txt`, `requirements-test.txt` : versions épinglées. `pytest-security` est commenté avec une explication. `fastapi` est ajouté à `requirements-test.txt`, car `backend/tests/test_api.py` importe `fastapi.testclient` : sans lui, la collecte échouait (`ModuleNotFoundError`).
- `backend/tests/test_api.py` : `TODO` passé en commentaire (1 ligne).
- `data_analysis_streamlit_app.py` : le commentaire d'en-tête pointe vers les variables `LLM_*` au lieu d'`OPENAI_API_KEY`.
- `.env.example` (nouveau) : variables `LLM_*` (Groq par défaut, exemple OpenAI).
- `maintainers/test_poc_smoke.py` (nouveau) : test de fumée pour les mainteneurs, hors du périmètre de l'examen (`backend/tests/` et `tests/` restent aux étudiants).

## Tests exécutés

| Commande | Résultat |
|---|---|
| `uv run --no-project --python 3.12 --with-requirements requirements.txt --with pytest==9.1.1 pytest -o addopts="" -p no:cacheprovider maintainers/` | **2 passed** : modèle et endpoint lus depuis l'env ; graphe du POC exécuté avec un modèle factice (appel `complete_python_task` sur un CSV, puis réponse finale) |
| `streamlit run data_analysis_streamlit_app.py` (headless) | `/_stcore/health` = `ok` |
| `streamlit.testing.AppTest` sur `Pages/python_visualisation_agent.py` | aucune exception |
| `pip install -r requirements.txt -r requirements-test.txt && pytest backend/tests/ -v` (commande de l'énoncé, venv neuf) | **1 passed, 19 skipped** (squelettes étudiants) |

Il n'existe **pas de solution de référence** dans le repo : les tests `backend/tests/*` sont des squelettes (`pytest.skip`) destinés aux étudiants.

## Points ouverts

- Aucun appel LLM réel n'a été fait (pas de clé valide ; la clé de la gateway Liora est refusée par LiteLLM, qui attend une clé `sk-...`).
- Avec OpenAI, le modèle choisi doit accepter le tool calling en Chat Completions. `gpt-6-luna` l'exige avec `reasoning_effort="none"`, un paramètre que le POC ne transmet pas.
- `pytest.ini` contient `asyncio_mode = auto` : sans `pytest-asyncio`, pytest affiche un avertissement. Fichier non modifié (fourni aux étudiants).
- Le chapitre 8 du cours (FR/EN) décrit toujours `pip install -r requirements.txt`, ce qui reste valable.
