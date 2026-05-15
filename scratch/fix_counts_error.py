import json

notebook_path = r'd:\PROJET_AURORAS\notebooks\01_discovery.ipynb'

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    source_str = "".join(cell.get('source', []))
    
    # 1. Clean up Cell 0 (Imports & Configuration)
    # It was trying to use 'df' and 'TARGET' before they were defined
    if 'counts    = df[TARGET]' in source_str:
        cell['source'] = [
            "import pandas as pd\n",
            "import numpy as np\n",
            "import matplotlib.pyplot as plt\n",
            "import matplotlib.patches as mpatches\n",
            "import seaborn as sns\n",
            "import warnings\n",
            "\n",
            "warnings.filterwarnings('ignore')\n",
            "\n",
            "# Style global des graphiques\n",
            "plt.style.use('seaborn-v0_8-darkgrid')\n",
            "sns.set_palette('husl')\n",
            "plt.rcParams['figure.figsize'] = (10, 5)\n",
            "plt.rcParams['font.size'] = 12\n",
            "\n",
            "# Configuration des couleurs\n",
            "COLOR_STORM   = '#800020'   # bordeaux (burgundy)\n",
            "COLOR_CALM    = '#1a237e'   # bleu nuit\n",
            "COLOR_ACCENT  = '#76ff03'   # vert aurore\n",
            "\n",
            "TARGET = 'is_storm'"
        ]

    # 2. Update Cell 1 (Chargement) to compute counts
    if "df = pd.read_csv('../data/dataset.csv')" in source_str:
        cell['source'] = [
            "df = pd.read_csv('../data/dataset.csv')\n",
            "print(f'Dataset chargé : {df.shape[0]:,} lignes × {df.shape[1]} colonnes')\n",
            "\n",
            "# Calcul immédiat des statistiques de classe pour les graphiques suivants\n",
            "counts = df[TARGET].value_counts().sort_index()\n",
            "pct_storm = (counts[1] / counts.sum() * 100) if 1 in counts else 0\n",
            "pct_calm  = (counts[0] / counts.sum() * 100) if 0 in counts else 0"
        ]

    # 3. Ensure Cell 6 (Visualisation) uses the correct variables
    if "values = [counts[0], counts[1]]" in source_str:
        # This cell looks fine as long as counts is defined
        pass

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Notebook code fixed: counts definition moved after df loading.")
