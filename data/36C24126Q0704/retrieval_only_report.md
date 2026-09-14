## Retrieval-only evaluation

Runs the real retrieval step directly against true_requirements.json + application.txt, bypassing extraction and verdict generation -- checks whether true_verdicts.json's own gold evidence quotes are among the chunks the verdict step would actually be shown.

**Evidence recall: 100.0% (20/20 gold evidence spans found in retrieved context, across 19 topics with gold evidence)**

- none (every gold evidence span was retrieved)