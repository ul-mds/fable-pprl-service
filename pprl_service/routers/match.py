import binascii
from itertools import product

import fable_core
from bitarray import bitarray
from fastapi import APIRouter, HTTPException
from fable_core.aggregation import AggregationFn
from fable_core.similarity import SimilarityFn
from fable_model import (
    SimilarityMeasure,
    VectorMatchRequest,
    VectorMatchResponse,
    Match,
    MatchMethod,
    SimilarityAggregator,
)
from starlette import status

router = APIRouter()

_similarity_mapping: dict[SimilarityMeasure, SimilarityFn] = {
    SimilarityMeasure.cosine: fable_core.similarity.cosine,
    SimilarityMeasure.dice: fable_core.similarity.dice,
    SimilarityMeasure.jaccard: fable_core.similarity.jaccard,
    SimilarityMeasure.russell_rao: fable_core.similarity.russell_rao,
    SimilarityMeasure.sokal_sneath: fable_core.similarity.sokal_sneath,
    SimilarityMeasure.sokal_michener: fable_core.similarity.sokal_michener,
    SimilarityMeasure.roger_tanimoto: fable_core.similarity.roger_tanimoto,
}

_aggregator_mapping: dict[SimilarityAggregator, AggregationFn] = {
    SimilarityAggregator.avg: fable_core.aggregation.average,
    SimilarityAggregator.max: fable_core.aggregation.maximum,
    SimilarityAggregator.min: fable_core.aggregation.minimum,
}


def _construct_bitarray_lookup_dict(match_req: VectorMatchRequest) -> dict[str, bitarray]:
    bitarray_lookup_dict: dict[str, bitarray] = {}
    failed_b64decode_entity_ids: set[str] = set()

    for bitarray_entity in match_req.domain + match_req.range:
        try:
            bitarray_lookup_dict[bitarray_entity.value] = fable_core.bits.from_base64(bitarray_entity.value)
        except (ValueError, binascii.Error):
            # from_base64 will throw a ValueError if invalid b64 is found
            failed_b64decode_entity_ids.add(bitarray_entity.id)

    if len(failed_b64decode_entity_ids) != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"invalid Base64 encoded bit vectors on entities with IDs {', '.join(failed_b64decode_entity_ids)}",
        )

    return bitarray_lookup_dict


@router.post("", response_model=VectorMatchResponse, status_code=status.HTTP_200_OK)
async def perform_matching(match_req: VectorMatchRequest) -> VectorMatchResponse:
    sim_measures = match_req.config.measures
    sim_method = match_req.config.method
    sim_fns = [_similarity_mapping.get(sim_measure) for sim_measure in sim_measures]
    agg_fn = _aggregator_mapping.get(match_req.config.aggregator)

    for i, sim_fn in enumerate(sim_fns):
        if sim_fn is None:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"unimplemented similarity measure `{sim_measures[i].name}`",
            )

    if match_req.config.aggregator != SimilarityAggregator.none and agg_fn is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"unimplemented aggregator `{match_req.config.aggregator.name}`",
        )

    bitarray_lookup = _construct_bitarray_lookup_dict(match_req)
    matches: list[Match] = []

    if sim_method == MatchMethod.crosswise:
        pairs = product(match_req.domain, match_req.range)
    elif sim_method == MatchMethod.pairwise:
        if len(match_req.domain) != len(match_req.range):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="length of domain and range lists do not match: domain has length of "
                f"{len(match_req.domain)}, range has length of {len(match_req.range)}",
            )
        pairs = zip(match_req.domain, match_req.range)
    else:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=f"unimplemented match method `{sim_method.name}`"
        )

    for domain_entity, range_entity in pairs:
        domain_ba = bitarray_lookup[domain_entity.value]
        range_ba = bitarray_lookup[range_entity.value]

        similarities = [sim_fn(domain_ba, range_ba) for sim_fn in sim_fns]

        if match_req.config.aggregator == SimilarityAggregator.none:
            agg_similarity = None
            is_match = all(
                [threshold <= similarity for threshold, similarity in zip(match_req.config.thresholds, similarities)]
            )
        else:
            try:
                agg_similarity = agg_fn(similarities, **match_req.config.aggregator_args)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"error while aggregating similarities: {e}",
                )
            is_match = match_req.config.thresholds[0] <= agg_similarity

        if is_match:
            matches.append(
                Match(
                    domain=domain_entity,
                    range=range_entity,
                    similarities=similarities,
                    aggregated_similarity=agg_similarity,
                )
            )

    return VectorMatchResponse(
        config=match_req.config,
        matches=matches,
    )
