from fable_model import (
    MatchConfig,
    SimilarityMeasure,
    VectorMatchRequest,
    VectorMatchResponse,
    Match,
    MatchMethod,
    SimilarityAggregator,
)
from starlette import status


def test_match_crosswise(test_client, bit_vector_entity_factory):
    exact_match_entity = bit_vector_entity_factory()
    config = MatchConfig(
        measures=SimilarityMeasure.jaccard,
        thresholds=1,
        method=MatchMethod.crosswise,
    )
    match_request = VectorMatchRequest(
        config=config,
        domain=[exact_match_entity, bit_vector_entity_factory()],
        range=[exact_match_entity, bit_vector_entity_factory()],
    )

    r = test_client.post("/match", json=match_request.model_dump())
    assert r.status_code == status.HTTP_200_OK

    match_response = VectorMatchResponse(**r.json())

    assert match_response.config == config
    assert match_response.matches == [
        Match(domain=exact_match_entity, range=exact_match_entity, similarities=[1], aggregated_similarity=None)
    ]


def test_match_pairwise(test_client, bit_vector_entity_factory):
    exact_match_entity = bit_vector_entity_factory()
    config = MatchConfig(
        measures=SimilarityMeasure.jaccard,
        thresholds=1,
        method=MatchMethod.pairwise,
    )
    match_request = VectorMatchRequest(
        config=config,
        domain=[exact_match_entity, bit_vector_entity_factory()],
        range=[exact_match_entity, bit_vector_entity_factory()],
    )

    r = test_client.post("/match", json=match_request.model_dump())
    assert r.status_code == status.HTTP_200_OK

    match_response = VectorMatchResponse(**r.json())

    assert match_response.config == config
    assert match_response.matches == [
        Match(domain=exact_match_entity, range=exact_match_entity, similarities=[1], aggregated_similarity=None)
    ]


def test_match_with_aggregator(test_client, bit_vector_entity_factory):
    exact_match_entity = bit_vector_entity_factory()
    config = MatchConfig(
        measures=[SimilarityMeasure.jaccard, SimilarityMeasure.sokal_michener, SimilarityMeasure.roger_tanimoto],
        thresholds=1,
        method=MatchMethod.pairwise,
        aggregator=SimilarityAggregator.avg,
    )
    match_request = VectorMatchRequest(
        config=config,
        domain=[exact_match_entity, bit_vector_entity_factory()],
        range=[exact_match_entity, bit_vector_entity_factory()],
    )

    r = test_client.post("/match", json=match_request.model_dump())
    assert r.status_code == status.HTTP_200_OK

    match_response = VectorMatchResponse(**r.json())

    assert match_response.config == config
    assert match_response.matches == [
        Match(domain=exact_match_entity, range=exact_match_entity, similarities=[1, 1, 1], aggregated_similarity=1)
    ]


def test_with_multiple_thresholds(test_client, bit_vector_entity_factory):
    exact_match_entity = bit_vector_entity_factory()
    config = MatchConfig(
        measures=[SimilarityMeasure.jaccard, SimilarityMeasure.sokal_michener, SimilarityMeasure.roger_tanimoto],
        thresholds=[1, 1, 1],
        method=MatchMethod.pairwise,
    )
    match_request = VectorMatchRequest(
        config=config,
        domain=[exact_match_entity, bit_vector_entity_factory()],
        range=[exact_match_entity, bit_vector_entity_factory()],
    )

    r = test_client.post("/match", json=match_request.model_dump())
    assert r.status_code == status.HTTP_200_OK

    match_response = VectorMatchResponse(**r.json())

    assert match_response.config == config
    assert match_response.matches == [
        Match(domain=exact_match_entity, range=exact_match_entity, similarities=[1, 1, 1], aggregated_similarity=None)
    ]


def test_match_400_on_invalid_base64(test_client, bit_vector_entity_factory):
    valid_entity, invalid_entity = bit_vector_entity_factory(), bit_vector_entity_factory()
    invalid_entity.value = "=A="  # invalid character for b64

    match_request = VectorMatchRequest(
        config=MatchConfig(
            measures=SimilarityMeasure.jaccard,
            thresholds=1,
        ),
        domain=[valid_entity],
        range=[invalid_entity],
    )

    r = test_client.post("/match", json=match_request.model_dump())
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert r.json()["detail"] == f"invalid Base64 encoded bit vectors on entities with IDs {invalid_entity.id}"


def test_match_400_on_pairwise_unmatched_list_lengths(test_client, bit_vector_entity_factory):
    match_request = VectorMatchRequest(
        config=MatchConfig(
            measures=SimilarityMeasure.jaccard,
            thresholds=1,
            method=MatchMethod.pairwise,
        ),
        domain=[bit_vector_entity_factory()] * 2,
        range=[bit_vector_entity_factory()] * 1,
    )

    r = test_client.post("/match", json=match_request.model_dump())
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert r.json()["detail"] == (
        "length of domain and range lists do not match: domain has length of 2, range has length of 1"
    )


def test_match_500_on_aggregation(test_client, bit_vector_entity_factory):
    match_request = VectorMatchRequest(
        config=MatchConfig(
            measures=[SimilarityMeasure.jaccard, SimilarityMeasure.sokal_michener, SimilarityMeasure.roger_tanimoto],
            thresholds=1,
            method=MatchMethod.pairwise,
            aggregator=SimilarityAggregator.avg,
            aggregator_args={"weights": [1, 2]},
        ),
        domain=[bit_vector_entity_factory()],
        range=[bit_vector_entity_factory()],
    )

    r = test_client.post("/match", json=match_request.model_dump())
    assert r.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert r.json()["detail"] == (
        "error while aggregating similarities: There need to be as many weights as there are similarities."
    )
