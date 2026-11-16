"""Cases and expected values of the review-workload tests."""

PROBLEM_COUNTS_AND_CATCHES = ((38, 37), (20, 19), (1, 1))
RANKED_PROBLEMS = 20
RANKED_COMPLIANT = 20
RANKED_READ = 19
TIED_LABELS = (True, True, False, False)
TIED_SCORES = (0.9, 0.5, 0.5, 0.1)
TIED_READ = 3
LAST_LABELS = (False, False, True)
LAST_SCORES = (0.9, 0.8, 0.1)
SEPARATED_SCORES = (0.9, 0.8, 0.2, 0.1)
EQUAL_SCORES = (0.5, 0.5, 0.5, 0.5)
CHANCE_AUC = 0.5
FOLDED_LABELS = (True, False, True, False)
FOLDED_SCORES = (0.9, 0.1, 0.2, 0.8)
FOLDED_FOLDS = (0, 0, 1, 1)
FOLDED_SAVED_WORK = 0.75
FOLDED_RECALL = 0.5
