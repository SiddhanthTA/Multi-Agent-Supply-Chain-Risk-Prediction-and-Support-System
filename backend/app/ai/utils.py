import numpy as np

from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
)


# --------------------------------------------------
# Compute Evaluation Metrics
# --------------------------------------------------

def compute_metrics(eval_pred):
    """
    Computes evaluation metrics for the Hugging Face Trainer.

    Returns:
        accuracy
        precision
        recall
        f1
    """

    logits, labels = eval_pred

    predictions = np.argmax(logits, axis=-1)

    precision, recall, f1, _ = precision_recall_fscore_support(
        labels,
        predictions,
        average="weighted",
        zero_division=0,
    )

    accuracy = accuracy_score(
        labels,
        predictions,
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }