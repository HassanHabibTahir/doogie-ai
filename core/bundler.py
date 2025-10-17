import json
import hashlib
from datetime import datetime

def create_pathway_bundle(pathway_json_str, condition_name="asthma"):
    """Make bundle JSON"""
    content_hash = hashlib.sha256(pathway_json_str.encode()).hexdigest()

    bundle = {
        "bundle_id": f"{condition_name}_pathway_bundle",
        "version": "3.0.0",
        "build": {
            "built_at": datetime.utcnow().isoformat(),
            "built_by": "DoogieAI",
            "content_sha256": content_hash
        },
        "pathway": pathway_json_str
    }

    output_path = f"data/{condition_name}_pathway_bundle.v3.0.0.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2, ensure_ascii=False)

    return output_path

