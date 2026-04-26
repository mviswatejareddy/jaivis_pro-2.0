from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np

try:
    import torch
except Exception:  # pragma: no cover
    torch = None


ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = ROOT / "src" / "jarvis" / "data" / "intents.json"
MODELS_DIR = ROOT / "models"


class IntentPredictor:
    def __init__(self) -> None:
        with DATA_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        self.intents = data["intents"]
        self.responses: Dict[str, List[str]] = {x["tag"]: x["responses"] for x in self.intents}

        self.ml_pipeline = None
        self.ml_labels: List[str] = []
        self.dl_bundle: Optional[dict] = None
        self.tf_bundle: Optional[dict] = None
        self.device = "cpu"
        self.dl_model = None
        self.tf_model = None
        if torch is not None and torch.cuda.is_available():
            self.device = "cuda"

        ml_path = MODELS_DIR / "intent_ml.joblib"
        if ml_path.exists():
            bundle = joblib.load(ml_path)
            self.ml_pipeline = bundle["pipeline"]
            self.ml_labels = bundle["labels"]

        dl_path = MODELS_DIR / "intent_dl.pt"
        if dl_path.exists() and torch is not None:
            self.dl_bundle = torch.load(dl_path, map_location=self.device)
        tf_path = MODELS_DIR / "intent_transformer.pt"
        if tf_path.exists() and torch is not None:
            self.tf_bundle = torch.load(tf_path, map_location=self.device)
        self._init_models()

    def _init_models(self) -> None:
        if torch is None:
            return
        if self.dl_bundle is not None:
            from .train_dl import NeuralIntentClassifier

            b = self.dl_bundle
            model = NeuralIntentClassifier(vocab_size=len(b["vocab"]), num_classes=len(b["labels"]))
            model.load_state_dict(b["state_dict"])
            model.to(self.device)
            model.eval()
            self.dl_model = model
        if self.tf_bundle is not None:
            from .train_transformer import TransformerIntentClassifier

            b = self.tf_bundle
            model = TransformerIntentClassifier(vocab_size=len(b["vocab"]), num_classes=len(b["labels"]))
            model.load_state_dict(b["state_dict"])
            model.to(self.device)
            model.eval()
            self.tf_model = model

    def _predict_ml(self, text: str) -> Tuple[str, float]:
        probs = self.ml_pipeline.predict_proba([text])[0]
        idx = int(np.argmax(probs))
        return self.ml_labels[idx], float(probs[idx])

    def _predict_dl(self, text: str) -> Tuple[str, float]:
        from .train_dl import encode_text

        bundle = self.dl_bundle
        vocab = bundle["vocab"]
        labels = bundle["labels"]
        max_len = bundle["max_len"]

        model = self.dl_model
        x = torch.tensor([encode_text(text, vocab, max_len)], dtype=torch.long, device=self.device)
        with torch.no_grad():
            logits = model(x)
            probs = torch.softmax(logits, dim=1).detach().cpu().numpy()[0]
        idx = int(np.argmax(probs))
        return labels[idx], float(probs[idx])

    def _predict_transformer(self, text: str) -> Tuple[str, float]:
        from .train_transformer import encode_text

        bundle = self.tf_bundle
        vocab = bundle["vocab"]
        labels = bundle["labels"]
        max_len = bundle["max_len"]

        model = self.tf_model
        x = torch.tensor([encode_text(text, vocab, max_len)], dtype=torch.long, device=self.device)
        with torch.no_grad():
            logits = model(x)
            probs = torch.softmax(logits, dim=1).detach().cpu().numpy()[0]
        idx = int(np.argmax(probs))
        return labels[idx], float(probs[idx])

    def predict(self, text: str) -> Tuple[str, float]:
        votes: Dict[str, float] = {}

        if self.ml_pipeline is not None:
            tag, conf = self._predict_ml(text)
            votes[tag] = votes.get(tag, 0.0) + (0.30 * conf)
        if self.dl_bundle is not None and torch is not None:
            tag, conf = self._predict_dl(text)
            votes[tag] = votes.get(tag, 0.0) + (0.35 * conf)
        if self.tf_bundle is not None and torch is not None:
            tag, conf = self._predict_transformer(text)
            votes[tag] = votes.get(tag, 0.0) + (0.35 * conf)

        if votes:
            best = max(votes, key=votes.get)
            return best, float(votes[best])
        return "fallback", 0.0

    def get_response(self, tag: str) -> str:
        options = self.responses.get(tag) or self.responses.get("fallback") or ["I am not sure how to help yet."]
        return random.choice(options)
