# Overview

There are 2 database + backend setups in this repo:
- Diagnosis DB (`diagnosis-{api,db}`)
- Exposure DB (not done yet)

## Terminology

- **TEK (Temporary Exposure Key)**: revolving key generated by user; covers a day?
    - `tek_i←CRNG(16)`
    - app stores `tek_i` and `i`
- **RPI (Rotating Proximity Indicator)**: rotated every ~15 minutes. Generated from `TEK`, and `ENIN`:
    - `RPIK_i←HKDF(tek_i,NULL,UTF8("EN-RPIK"),16)`
    - `RPI_i,j←AES128(RPIK_i,PaddedData_j)`
    - `PaddedData_j[0...5]=UTF8("EN-RPI")`
    - `PaddedData_j[6...11]=0x000000000000`
    - `PaddedData_j[12...15]=ENIN_j`
- **ENIN (ENIntervalNumber)**: UTC timestamp / 10:
    - ENIntervalNumber(Timestamp)←Timestamp/60×10
- **HA (Health Authority)**: an administrative entity with the ability to diagnose a `Report Key` as a confirmed case
- **Report**: a set of diagnosed `TEK`s uploaded to the diagnosis database

Key types:
- **Report Key**: a key that is reported to backend or HA (usually in a batch)
- **Diagnosis Key**: a `TEK` that is confirmed to correspond to a positive diagnosis
- **Exposure Key**: a `TEK` that has been exposed to a `diagnosis key`: e.g. an entity notices an overlap in RPI-space with a diagnosed `TEK` and publishes its own `TEK` for that period. What lighthouses need
- **Self-diagnosis Key**: a `TEK` that corresponds to an unconfirmed positive diagnosis
- **HAK (Health Authority Key)**: a public key associated with a health authority
- **LHK (Lighthouse Key)**: a unique identifier associated with a lighthouse


## Setup

To run the development setup (postgres backend defined in `*-db/`, API backend defined in `*-db/`), use docker-compose:

```
docker-compose up
```

This should bring up:
- Diagnosis Postgres backend (port 5434)
- Diagnosis Postgres API (port 5000)


## Reporting (DiagnosisDB)

The diagnosis backend receives TEKs (with timestamps marking the beginning of their 'valid' period) that have been "tainted" by an authority. This authority is trusted to perform a diagnosis of the entity who possesses the TEKs.

Currently we are using a random 16-byte key as the "API key" for an authority. There are two authorities loaded into the database at start:
- `2iUNf7/8pjS/mzjpQwUIuw==`
- `V3Qpwr4TU7CICdwowL9rwA==`

Reports have the following JSON schema and are POST-ed to `/add-report`

```json
{
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "authority": {"type": "string"},
        "reports": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "TEK": {"type": "string"},
                    "ENIN": {"type": "integer"}
                }
            }
        },
        "metadata": {"type": "object"}
    }
}
```

All binary data (TEKs and authority keys) are encoded with base64 for transit.

**Example**: see `diagnosis-api/post.py`

## Querying (DiagnosisDB)

To get started, there is only one way of getting the data out. Do a GET to `/get-diagnosis-keys` to get a big JSON dump of every (TEK, ENIN) tuple in the backend

See `diagnosis-db/get.py` for an example.

```json
[
    {
        "ENIN": 2647301,
        "TEK": "22mUXq6CNLZRhXa3h0/oDA=="
    },
    {
        "ENIN": 2647302,
        "TEK": "U3hF8iVln6ZUn5/de2rqNg=="
    },
    {
        "ENIN": 2647303,
        "TEK": "TtFYrla3/g7biOosDxQrZQ=="
    },
    {
        "ENIN": 2647304,
        "TEK": "ulZoE4vMcQV9zMXdFiqX7Q=="
    }
]
```