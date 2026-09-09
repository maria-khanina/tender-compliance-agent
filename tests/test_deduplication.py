from steps.deduplication import _cluster_by_similarity


def test_similar_vectors_are_grouped_together() -> None:
    embedding_vectors = [
        [1.0, 0.0, 0.0],
        [0.99, 0.01, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.98, 0.02],
        [0.0, 0.0, 1.0],
    ]
    clusters = _cluster_by_similarity(embedding_vectors)
    normalized_clusters = []
    for cluster in clusters:
        normalized_clusters.append(sorted(cluster))
    normalized_clusters.sort()
    assert normalized_clusters == [[0, 1], [2, 3], [4]]
