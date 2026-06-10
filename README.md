![GitHub Release](https://img.shields.io/github/v/release/ul-mds/fable-pprl-service)
![Code Coverage](https://img.shields.io/badge/Coverage-92%25-green.svg)
![License](https://img.shields.io/github/license/ul-mds/fable-pprl-service)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white)](https://conventionalcommits.org)

# FABLE PPRL Service

This package implements an HTTP service for PPRL based on Bloom filters used in the FABLE (**F**ederated
**A**nonymized **B**loom filter **L**inkage **E**ngine) ecosystem.
It covers the preprocessing and masking of records, as well as matching on masked records.
The service is built with [FastAPI](https://fastapi.tiangolo.com/).

## Deployment

```bash
docker run -p 8080:8080 -e ROLE=both ghcr.io/ul-mds/fable-pprl-service:latest
```

See the [Configuration section](#configuration) for more details on all available options.

## Service endpoints

The service exposes each of the aforementioned steps as an endpoint each.
Their behavior is freely configurable.

### Record preprocessing

`/transform` enables preprocessing of records using a variety of transformers that can be applied to record fields.
These transformers can be applied to all attributes ("globally") or to single attributes.

```python
import httpx
import json

r = httpx.post("http://localhost:8000/transform/", json={
    "config": {
        "empty_value": "error"
    },
    "entities": [
        {
            "id": "001",
            "attributes": {
                "given_name": "John",
                "last_name": "Doe",
                "date_of_birth": "05.06.1978",
                "gender": "male"
            }
        }
    ],
    "global_transformers": {
        "before": [
            {
                "name": "normalization"
            }
        ]
    },
    "attribute_transformers": [
        {
            "attribute_name": "date_of_birth",
            "transformers": [
                {
                    "name": "date_time",
                    "input_format": "%d.%m.%Y",
                    "output_format": "%Y-%m-%d"
                }
            ]
        },
        {
            "attribute_name": "gender",
            "transformers": [
                {
                    "name": "mapping",
                    "mapping": {
                        "male": "m",
                        "female": "f"
                    },
                    "default_value": "x"
                }
            ]
        }
    ]
})

assert r.status_code == 200

print(json.dumps(r.json()["entities"], indent=2))
```

```console
[
  {
    "id": "001",
    "attributes": {
      "given_name": "john",
      "last_name": "doe",
      "date_of_birth": "1978-06-05",
      "gender": "m"
    }
  }
]
```

### Record masking

`/mask` enables masking of records based on Bloom filter techniques.
It supports a variety of encoding and hardening methods, as well as control over various bit vector generation
parameters.

```python
import httpx
import json

r = httpx.post("http://localhost:8000/mask/", json={
    "config": {
        "token_size": 2,
        "hash": {
            "function": {
                "algorithms": ["sha1"],
                "key": "s3cr3t_k3y"
            },
            "strategy": {
                "name": "random_hash"
            }
        },
        "filter": {
            "type": "clk",
            "filter_size": 512,
            "hash_values": 5
        },
        "prepend_attribute_name": True,
        "padding": "_",
        "hardeners": [
            {
                "name": "rehash",
                "window_size": 8,
                "window_step": 4,
                "samples": 2
            }
        ]
    },
    "entities": [
        {
            "id": "001",
            "attributes": {
                "given_name": "jon",
                "last_name": "doe",
                "date_of_birth": "1978.06.05",
                "gender": "m"
            }
        }
    ],
    "attributes": [
        {
            "attribute_name": "given_name",
            "salt": {
                "value": "my_s33d"
            }
        }
    ]
})

assert r.status_code == 200
print(json.dumps(r.json()["entities"], indent=2))
```

```console
[
  {
    "id": "001",
    "value": "QBBAYOEBgFOKMREGBAZxDSfAQKGEEAJyydB4bQO6dl4gc58EJEgiAZCVgwGCoDSXA6GIA4ODkQEgEAQEhQAgJA=="
  }
]
```

### Bit vector matching

`/match` enables the computation of similarities between bit vector pairs.
It implements different similarity measures and aggregation methods if multiple similarity measures are defined.

```python
import httpx
import json

r = httpx.post("http://localhost:8000/match/", json={
    "config": {
        "measures": ["jaccard", "cosine"],
        "thresholds": 0.7,
        "aggregator": "avg",
        "aggregator_args": {
            "weights": [2, 1]
        }
    },
    "domain": [
        {
            "id": "D001",
            "value": "RBDAZOkBgFOKMQGGBAJxDSfAQKCAGADyqbB+bQu6cjIkc58MJEgqBbCVgwGCoTSTA6WJA4IDkQEgEQYshQEgLA=="
        },
        {
            "id": "D002",
            "value": "wsJiLptLjVHKvcoMZIR7NS3JaikIMNJiaqRKPOKaZMQEcjsp4ShuEVqSiRU0jTQWB6FIgSKikAAgEW7kpXNMsw=="
        }
    ],
    "range": [
        {
            "id": "R001",
            "value": "AZCMTgvQAUPImaYEaNdzBwXDGHHEDAM+pJH0L5DWdWgUY/4IJkluETLACSGytaDWA7UwhSKSUQBAEIQstQXUXA=="
        },
        {
            "id": "R002",
            "value": "QBBAYOEBgFOKMREGBAZxDSfAQKGEEAJyydB4bQO6dl4gc58EJEgiAZCVgwGCoDSXA6GIA4ODkQEgEAQEhQAgJA=="
        }
    ]
})

assert r.status_code == 200
print(json.dumps(r.json()["matches"], indent=2))
```

```console
[
  {
    "domain": {
      "id": "D001",
      "value": "RBDAZOkBgFOKMQGGBAJxDSfAQKCAGADyqbB+bQu6cjIkc58MJEgqBbCVgwGCoTSTA6WJA4IDkQEgEQYshQEgLA=="
    },
    "range": {
      "id": "R002",
      "value": "QBBAYOEBgFOKMREGBAZxDSfAQKGEEAJyydB4bQO6dl4gc58EJEgiAZCVgwGCoDSXA6GIA4ODkQEgEAQEhQAgJA=="
    },
    "similarities": [
      0.7771739130434783,
      0.8753097187762677
    ],
    "aggregated_similarity": 0.8098858482877415
  }
]
```

## Configuration

The following table shows all available configuration options.
These variables can be defined in `.env`.

| **Environment variable** | **Description**                                                                                                | **Default** |
|--------------------------|----------------------------------------------------------------------------------------------------------------|-------------|
| ROLE                     | Defines which endpoints are published. Needs to be either `both`, `data_owner` or `linkage_unit`.<sup>1)</sup> |             |

<sup>1)</sup> If set to `data_owner`, the endpoints for transforming and masking are published, while `linkage_unit` will only publish the endpoint for matching.

## License

MIT.
