#!/usr/bin/env python3
"""
Speaker registry for voice embedding extraction and matching.
Uses pyannote's embedding model to create voice fingerprints.
"""

import json
import argparse
from pathlib import Path
import numpy as np


def cosine_similarity(a, b):
    """Compute cosine similarity between two vectors."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def main():
    ap = argparse.ArgumentParser(description="Speaker registry operations")
    ap.add_argument("action", choices=["init", "list", "add-sample", "match"])
    ap.add_argument("--registry", default="speaker_registry.json")
    ap.add_argument("--name", help="Speaker name for add-sample")
    ap.add_argument("--embedding", help="Embedding JSON file for add-sample")
    ap.add_argument("--embedding-dir", help="Directory with embedding files")
    ap.add_argument("--top-k", type=int, default=3, help="Top matches to return")
    args = ap.parse_args()
    
    registry_path = Path(args.registry)
    
    if args.action == "init":
        # Initialize empty registry
        registry = {"speakers": {}}
        registry_path.write_text(json.dumps(registry, indent=2))
        print(f"Created empty registry at {registry_path}")
        
    elif args.action == "list":
        if not registry_path.exists():
            print("Registry not found. Run 'init' first.")
            return
        registry = json.loads(registry_path.read_text())
        speakers = registry.get("speakers", {})
        if not speakers:
            print("No speakers registered.")
        else:
            print(f"Registered speakers ({len(speakers)}):")
            for name, data in speakers.items():
                samples = data.get("samples", [])
                print(f"  {name}: {len(samples)} sample(s)")
                
    elif args.action == "add-sample":
        if not args.name or not args.embedding:
            print("Require --name and --embedding")
            return
        if not registry_path.exists():
            registry = {"speakers": {}}
        else:
            registry = json.loads(registry_path.read_text())
        
        embedding = json.loads(Path(args.embedding).read_text())
        vector = embedding.get("embedding", [])
        
        if args.name not in registry["speakers"]:
            registry["speakers"][args.name] = {"samples": []}
        
        registry["speakers"][args.name]["samples"].append({
            "source": args.embedding,
            "embedding": vector
        })
        
        # Compute average embedding
        all_vectors = [s["embedding"] for s in registry["speakers"][args.name]["samples"]]
        avg = np.mean(all_vectors, axis=0).tolist()
        registry["speakers"][args.name]["average_embedding"] = avg
        
        registry_path.write_text(json.dumps(registry, indent=2))
        print(f"Added sample for {args.name} ({len(all_vectors)} total samples)")
        
    elif args.action == "match":
        if not args.embedding_dir:
            print("Require --embedding-dir")
            return
        if not registry_path.exists():
            print("Registry not found. Run 'init' and add speakers first.")
            return
        
        registry = json.loads(registry_path.read_text())
        speakers = registry.get("speakers", {})
        
        if not speakers:
            print("No speakers in registry.")
            return
        
        # Load embeddings to match
        embedding_dir = Path(args.embedding_dir)
        results = []
        
        for emb_file in embedding_dir.glob("*.json"):
            emb_data = json.loads(emb_file.read_text())
            vector = emb_data.get("embedding", [])
            speaker_id = emb_data.get("speaker", emb_file.stem)
            
            # Compare against all registered speakers
            scores = {}
            for name, data in speakers.items():
                avg = data.get("average_embedding", [])
                if avg:
                    scores[name] = cosine_similarity(vector, avg)
            
            best_match = max(scores, key=scores.get) if scores else None
            results.append({
                "file": str(emb_file),
                "speaker_id": speaker_id,
                "best_match": best_match,
                "score": scores.get(best_match, 0),
                "all_scores": scores
            })
        
        # Print top results
        results.sort(key=lambda x: x["score"], reverse=True)
        for r in results[:args.top_k]:
            print(f"{r['speaker_id']} -> {r['best_match']} ({r['score']:.3f})")


if __name__ == "__main__":
    main()
