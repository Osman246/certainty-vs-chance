# Hand-labelling guide (your "gold standard")

Claude's labels only count if they agree with a careful human. That human is you.

1. **Draw a random sample of 200 posts** before you look at any Claude labels (blind):
   ```bash
   python -c "import pandas as pd; p=pd.read_csv('data/raw/posts.csv'); p.sample(200, random_state=1)[['id','text']].assign(reward_type='',stance='',money_pressure='').to_csv('data/labels/human_todo.csv', index=False)"
   ```
2. Open `human_todo.csv` in Excel or Numbers and fill in the three columns using **only** the labels in `config/codebook.yaml`.
3. Save it as `data/labels/human.csv`.
4. Run `python -m cvc.validate` (with `PYTHONPATH=src`).

**Reading kappa:** 0.8+ strong · 0.6-0.8 substantial · below 0.6 means a definition is unclear. Fix the codebook, relabel and log the change.

**Pilot first:** label 50, run Claude on the same 50 (`--limit`), and read every disagreement. Most come from fuzzy definitions, not from the model. Tighten the codebook *before* the full run, and record which version you used (`version:` in codebook.yaml).

**Arabic posts:** if you can't read them confidently, leave them out of the gold sample and say so in the limitations. Don't guess.
