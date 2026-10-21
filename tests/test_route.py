import json
from api.railway_api import plan_route

result = plan_route(
    stops=[
        {"station": "CSMT"},
        {"station": "NDLS"},
    ],
    max_transfers=1,
)


print(json.dumps(result, indent=2, ensure_ascii=False))