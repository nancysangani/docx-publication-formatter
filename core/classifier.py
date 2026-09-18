"""
Element Classifier
-------------------
Tags every parsed block as one of:
    Title, Heading, Subheading, Body, Caption, Reference, List, Table

Hybrid design (explainable, not a black box):
  1. High-precision RULES fire first for unambiguous cases (e.g. a table is
     always "Table"; a line starting with "Fig." is almost always "Caption").
  2. For everything else, a lightweight Random Forest — trained here on a
     programmatically generated synthetic dataset that encodes the same
     editorial conventions as the rules — predicts the label and returns a
     confidence score.
  3. Predictions below CONFIDENCE_THRESHOLD are flagged for manual review
     instead of being silently applied — this is what keeps the pipeline
     safe on ambiguous input while staying fully automatic on clear cases.

The synthetic training set is a bootstrap: it lets the classifier run today
without requiring a hand-labeled manuscript corpus. Swap `_synthetic_training_data()`
for real labeled manuscripts as they become available — the rest of the
pipeline does not need to change.
"""

import random
from sklearn.ensemble import RandomForestClassifier
from core.features import block_to_features, FEATURE_NAMES

LABELS = ["Title", "Heading", "Subheading", "Body", "Caption", "Reference", "List", "Table"]
CONFIDENCE_THRESHOLD = 0.55


def _synthetic_training_data(n_per_class=400, seed=42):
    """Generate synthetic (features, label) pairs that encode the same
    editorial conventions used in the rule layer, so the model learns a
    consistent, explainable decision boundary."""
    rng = random.Random(seed)
    X, y = [], []

    def add(label, font_size, bold, italic, indent, caps, num, figtab, words, pos, table=0.0):
        X.append([font_size, bold, italic, indent, caps, num, figtab, min(words, 200) / 200.0, pos, table])
        y.append(label)

    for _ in range(n_per_class):
        # Title: large font, bold, near start of doc, few words
        add("Title", rng.uniform(18, 28), 1.0, 0.0, 0.0, rng.choice([0, 1]), 0.0, 0.0,
            rng.randint(1, 8), rng.uniform(0, 0.03))
        # Heading: 16pt+ bold, short line, chapter/number pattern common
        add("Heading", rng.uniform(15, 20), 1.0, 0.0, 0.0, 0.0, rng.choice([0, 1]), 0.0,
            rng.randint(1, 8), rng.uniform(0, 1))
        # Subheading: 12-14pt bold, short
        add("Subheading", rng.uniform(12, 14.5), 1.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            rng.randint(1, 10), rng.uniform(0, 1))
        # Body: 10-12pt regular, long paragraph, some indent
        add("Body", rng.uniform(10, 12.5), 0.0, 0.0, rng.uniform(0, 1.5), 0.0, 0.0, 0.0,
            rng.randint(20, 200), rng.uniform(0, 1))
        # Caption: small italic, starts with fig/table pattern
        add("Caption", rng.uniform(9, 11), 0.0, 1.0, 0.0, 0.0, 0.0, 1.0,
            rng.randint(2, 20), rng.uniform(0, 1))
        # Reference: hanging indent, numbered pattern, near end of doc
        add("Reference", rng.uniform(10, 11), 0.0, 0.0, rng.uniform(0.5, 1.5), 0.0, 1.0, 0.0,
            rng.randint(10, 40), rng.uniform(0.7, 1.0))
        # List: short numbered/bulleted lines, moderate indent
        add("List", rng.uniform(10, 12), 0.0, 0.0, rng.uniform(0.3, 1.2), 0.0, 1.0, 0.0,
            rng.randint(2, 15), rng.uniform(0, 1))
        # Table: handled almost entirely by the rule layer; included for completeness
        add("Table", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, rng.randint(1, 100), rng.uniform(0, 1), table=1.0)

    return X, y


class ElementClassifier:
    def __init__(self):
        X, y = _synthetic_training_data()
        self.model = RandomForestClassifier(
            n_estimators=200, max_depth=None, random_state=42
        )
        self.model.fit(X, y)

    # ---- Rule layer -----------------------------------------------------
    @staticmethod
    def _rule_based_label(block, total_blocks):
        if block["type"] == "table":
            return "Table", 1.0

        text = block["text"].strip()
        text_upper = text.upper()
        font_size = block["font_size"] or 0
        position_ratio = block["index"] / max(total_blocks - 1, 1)

        if block["starts_with_fig_table"]:
            return "Caption", 0.9

        if position_ratio < 0.02 and font_size >= 18 and block["bold"]:
            return "Title", 0.92

        if font_size >= 15.5 and block["bold"]:
            return "Heading", 0.88

        # FIX 1: Universal Chapter Interceptor (Handles "CHAPTER", "chapter", "ChApTeR")
        if text_upper.startswith("CHAPTER ") and block["word_count"] <= 12:
            return "Heading", 0.95
            
        # Alternative fallback check for numbered chapter headers
        if block["starts_with_number"] and block["is_all_caps"] and block["word_count"] <= 12:
            return "Heading", 0.85

        # FIX 2: Bulletproof Dialogue Check (Catches short lines like "Look out!" instantly)
        if text.startswith(('"', "'", '“', '‘')) or text.endswith(('"', "'", '”', '’')):
            return "Body", 0.95

        # FIX 3: Bracketed Global Reference Catch (Overrides positional boundaries)
        if text.startswith('[') and ']' in text and 'Reference' in text:
            return "Reference", 0.90

        # Standard Divider Symbol Check
        if len(text) <= 6 and text and all(ch in "*-—_. " for ch in text):
            return "Body", 0.95

        if block["starts_with_number"] and position_ratio > 0.6 and block["word_count"] > 8:
            return "Reference", 0.75

        # Regular Prose Paragraphs
        if (not block["bold"] and not block["italic"] and not block["starts_with_fig_table"]
                and not block["starts_with_number"] and block["word_count"] >= 6):
            return "Body", 0.9

        return None, 0.0  # defer to the ML model


    # ---- Public API -------------------------------------------------------
    def classify(self, block, total_blocks):
        label, confidence = self._rule_based_label(block, total_blocks)
        method = "rule"

        if label is None:
            feats = block_to_features(block, total_blocks)
            probs = self.model.predict_proba([feats])[0]
            best_idx = probs.argmax()
            label = self.model.classes_[best_idx]
            confidence = float(probs[best_idx])
            method = "model"

        needs_review = confidence < CONFIDENCE_THRESHOLD
        return {
            "label": label,
            "confidence": round(confidence, 3),
            "method": method,
            "needs_review": needs_review,
        }

    def classify_all(self, blocks):
        """Batched classification: rules resolve the clear cases instantly;
        only the remaining ambiguous blocks go through a single batched
        model.predict_proba call, instead of one Python-level call per
        block. This is what keeps a 400+ page manuscript (thousands of
        blocks) processing in seconds rather than minutes."""
        total = len(blocks)
        results = [None] * total
        deferred_indices = []
        deferred_feats = []

        for i, b in enumerate(blocks):
            label, confidence = self._rule_based_label(b, total)
            if label is not None:
                results[i] = {**b, "label": label, "confidence": confidence,
                               "method": "rule", "needs_review": confidence < CONFIDENCE_THRESHOLD}
            else:
                deferred_indices.append(i)
                deferred_feats.append(block_to_features(b, total))

        if deferred_feats:
            probs_batch = self.model.predict_proba(deferred_feats)
            best_idx = probs_batch.argmax(axis=1)
            for j, i in enumerate(deferred_indices):
                label = self.model.classes_[best_idx[j]]
                confidence = float(probs_batch[j, best_idx[j]])
                results[i] = {**blocks[i], "label": label, "confidence": confidence,
                               "method": "model", "needs_review": confidence < CONFIDENCE_THRESHOLD}

        return results
