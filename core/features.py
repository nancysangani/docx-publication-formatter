"""
Feature engineering — converts a parsed block into a numeric feature vector
the classifier can use. These are exactly the signals a human editor would
look at: font size, boldness, indentation, position, and simple text
patterns. No black-box embeddings — every feature here is directly
inspectable, which is what makes the classifier's decisions explainable.
"""

FEATURE_NAMES = [
    "font_size",
    "is_bold",
    "is_italic",
    "indent_cm",
    "is_all_caps",
    "starts_with_number",
    "starts_with_fig_table",
    "word_count",
    "position_ratio",   # 0.0 = start of doc, 1.0 = end of doc
    "is_table",
]


def block_to_features(block, total_blocks):
    font_size = block["font_size"] if block["font_size"] else 12.0
    position_ratio = block["index"] / max(total_blocks - 1, 1)
    return [
        font_size,
        1.0 if block["bold"] else 0.0,
        1.0 if block["italic"] else 0.0,
        block["indent_cm"],
        1.0 if block["is_all_caps"] else 0.0,
        1.0 if block["starts_with_number"] else 0.0,
        1.0 if block["starts_with_fig_table"] else 0.0,
        min(block["word_count"], 200) / 200.0,  # normalized
        position_ratio,
        1.0 if block["type"] == "table" else 0.0,
    ]
