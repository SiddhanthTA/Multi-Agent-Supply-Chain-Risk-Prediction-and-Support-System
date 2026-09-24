from transformers import pipeline

from app.utils.logger import logger


class AIRelevanceFilter:
    """
    AI-powered relevance filter for supply-chain risk intelligence.

    The filter uses three semantic checks:

    1. Disruption evidence
    2. Supply-chain impact
    3. Routine/general-news exclusion

    In addition to individual scores, the classifier compares
    the winning label against the competing label. This reduces
    false positives caused by weak semantic differences.

    No model training is required.
    """

    def __init__(self):

        logger.info("Loading AI Relevance Filter...")

        self.classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
        )

        logger.info(
            "AI Relevance Filter Loaded Successfully."
        )

        # ==================================================
        # STAGE 1
        # DISRUPTION EVIDENCE
        # ==================================================

        self.disruption_labels = [
            (
                "a concrete actual or potential disruptive event "
                "that causes or threatens a shortage, delay, "
                "blockage, shutdown, interruption, restriction, "
                "supplier failure, transportation failure, "
                "production failure, or significant supply risk"
            ),
            (
                "an article that does not describe a concrete "
                "actual or potential disruptive event"
            ),
        ]

        # ==================================================
        # STAGE 2
        # SUPPLY-CHAIN IMPACT
        # ==================================================

        self.impact_labels = [
            (
                "a disruption or risk that directly affects "
                "sourcing, production, manufacturing, inventory, "
                "procurement, transportation, logistics, trade, "
                "delivery, availability, or movement of goods, "
                "materials, components, energy, or resources"
            ),
            (
                "an event with no meaningful impact on supply "
                "chain operations, goods, materials, resources, "
                "production, transportation, or availability"
            ),
        ]

        # ==================================================
        # STAGE 3
        # ROUTINE NEWS EXCLUSION
        # ==================================================

        self.routine_labels = [
            (
                "routine business, financial, investment, "
                "technology, research, corporate, political, "
                "market, or general news that does not report "
                "a supply chain disruption or supply chain risk"
            ),
            (
                "news reporting an actual or potential supply "
                "chain disruption or significant supply chain risk"
            ),
        ]

        # ==================================================
        # THRESHOLDS
        # ==================================================

        self.disruption_threshold = 0.65
        self.impact_threshold = 0.65
        self.exclusion_threshold = 0.65

        # Minimum difference between the winning and
        # competing semantic class.
        self.disruption_margin = 0.15
        self.impact_margin = 0.15
        self.routine_margin = 0.15

        # Final combined confidence.
        self.final_threshold = 0.68

    # ======================================================
    # ZERO-SHOT CLASSIFICATION
    # ======================================================

    def _classify(
        self,
        text: str,
        labels: list,
        hypothesis_template: str,
    ) -> dict:
        """
        Run zero-shot classification and return both the
        winning score and the competing score.
        """

        result = self.classifier(
            text,
            candidate_labels=labels,
            multi_label=False,
            hypothesis_template=hypothesis_template,
        )

        scores = result["scores"]
        labels_result = result["labels"]

        top_label = labels_result[0]
        top_score = float(scores[0])

        # Since this is a two-class classifier, the second
        # score is the competing semantic interpretation.
        competing_score = float(scores[1])

        margin = top_score - competing_score

        return {
            "label": top_label,
            "score": top_score,
            "competing_score": competing_score,
            "margin": margin,
        }

    # ======================================================
    # EVALUATE ARTICLE
    # ======================================================

    def evaluate(self, text: str) -> dict:
        """
        Determine whether an article represents an actual
        or potential supply-chain disruption.

        Returns:

        {
            "accepted": bool,
            "score": float,
            "label": str,
            "reason": str
        }
        """

        # ==================================================
        # INPUT VALIDATION
        # ==================================================

        if not text or not text.strip():

            logger.warning(
                "[AI FILTER] Empty article text received."
            )

            return {
                "accepted": False,
                "score": 0.0,
                "label": "Not supply chain relevant",
                "reason": "Article text is empty",
            }

        # ==================================================
        # NORMALIZE INPUT
        # ==================================================

        text = text.strip()

        if len(text) > 4000:
            text = text[:4000]

        # ==================================================
        # STAGE 1
        # DISRUPTION EVIDENCE
        # ==================================================

        disruption_result = self._classify(
            text=text,
            labels=self.disruption_labels,
            hypothesis_template="This article describes {}.",
        )

        disruption_score = disruption_result["score"]
        disruption_competing = disruption_result["competing_score"]
        disruption_margin = disruption_result["margin"]

        disruption_detected = (
            disruption_result["label"]
            == self.disruption_labels[0]
            and disruption_score
            >= self.disruption_threshold
            and disruption_margin
            >= self.disruption_margin
        )

        logger.info(
            f"[AI FILTER] Stage 1 | "
            f"Disruption={disruption_score:.4f} | "
            f"Opposite={disruption_competing:.4f} | "
            f"Margin={disruption_margin:.4f} | "
            f"Detected={disruption_detected}"
        )

        # --------------------------------------------------
        # REJECT IF DISRUPTION EVIDENCE IS WEAK
        # --------------------------------------------------

        if not disruption_detected:

            reason = (
                "Insufficient semantic evidence of an actual "
                "or potential disruptive event"
            )

            logger.info(
                f"[AI FILTER] Rejected | "
                f"Reason={reason}"
            )

            return {
                "accepted": False,
                "score": round(disruption_score, 4),
                "label": "Not supply chain relevant",
                "reason": reason,
            }

        # ==================================================
        # STAGE 2
        # SUPPLY-CHAIN IMPACT
        # ==================================================

        impact_result = self._classify(
            text=text,
            labels=self.impact_labels,
            hypothesis_template="This article describes {}.",
        )

        impact_score = impact_result["score"]
        impact_competing = impact_result["competing_score"]
        impact_margin = impact_result["margin"]

        supply_chain_impact = (
            impact_result["label"]
            == self.impact_labels[0]
            and impact_score
            >= self.impact_threshold
            and impact_margin
            >= self.impact_margin
        )

        logger.info(
            f"[AI FILTER] Stage 2 | "
            f"Impact={impact_score:.4f} | "
            f"Opposite={impact_competing:.4f} | "
            f"Margin={impact_margin:.4f} | "
            f"SupplyChainImpact={supply_chain_impact}"
        )

        # --------------------------------------------------
        # REJECT IF IMPACT IS WEAK
        # --------------------------------------------------

        if not supply_chain_impact:

            reason = (
                "Disruption evidence exists, but the article "
                "does not show sufficiently strong direct "
                "supply-chain impact"
            )

            logger.info(
                f"[AI FILTER] Rejected | "
                f"Reason={reason}"
            )

            return {
                "accepted": False,
                "score": round(
                    min(
                        disruption_score,
                        impact_score,
                    ),
                    4,
                ),
                "label": "Insufficient supply chain impact",
                "reason": reason,
            }

        # ==================================================
        # STAGE 3
        # ROUTINE NEWS EXCLUSION
        # ==================================================

        routine_result = self._classify(
            text=text,
            labels=self.routine_labels,
            hypothesis_template="This article is {}.",
        )

        routine_score = routine_result["score"]
        routine_competing = routine_result["competing_score"]
        routine_margin = routine_result["margin"]

        is_routine_news = (
            routine_result["label"]
            == self.routine_labels[0]
            and routine_score
            >= self.exclusion_threshold
            and routine_margin
            >= self.routine_margin
        )

        logger.info(
            f"[AI FILTER] Stage 3 | "
            f"Routine={routine_score:.4f} | "
            f"Opposite={routine_competing:.4f} | "
            f"Margin={routine_margin:.4f} | "
            f"RoutineNews={is_routine_news}"
        )

        # --------------------------------------------------
        # REJECT ROUTINE NEWS
        # --------------------------------------------------

        if is_routine_news:

            reason = (
                "Article is semantically classified as "
                "routine business, financial, investment, "
                "technology, research, political, market, "
                "or general news rather than a meaningful "
                "supply-chain disruption"
            )

            logger.info(
                f"[AI FILTER] Rejected | "
                f"Reason={reason}"
            )

            return {
                "accepted": False,
                "score": round(
                    min(
                        disruption_score,
                        impact_score,
                    ),
                    4,
                ),
                "label": "Routine or general news",
                "reason": reason,
            }

        # ==================================================
        # FINAL COMBINED SCORE
        # ==================================================

        # Routine score is inverted because a LOW routine
        # score is desirable for a supply-chain disruption.

        non_routine_score = 1.0 - routine_score

        final_score = (
            (disruption_score * 0.40)
            + (impact_score * 0.40)
            + (non_routine_score * 0.20)
        )

        # ==================================================
        # FINAL ACCEPTANCE
        # ==================================================

        accepted = (
            final_score >= self.final_threshold
        )

        logger.info(
            f"[AI FILTER] Final Decision | "
            f"FinalScore={final_score:.4f} | "
            f"Threshold={self.final_threshold:.2f} | "
            f"Accepted={accepted}"
        )

        # --------------------------------------------------
        # FINAL REJECTION
        # --------------------------------------------------

        if not accepted:

            reason = (
                "Article passed the individual semantic checks "
                "but the combined relevance confidence was "
                "not strong enough"
            )

            logger.info(
                f"[AI FILTER] Rejected | "
                f"Reason={reason}"
            )

            return {
                "accepted": False,
                "score": round(final_score, 4),
                "label": "Low combined relevance",
                "reason": reason,
            }

        # ==================================================
        # FINAL ACCEPTANCE
        # ==================================================

        reason = (
            "Article describes an actual or potential "
            "supply-chain disruption with meaningful impact"
            f" | Disruption={disruption_score:.4f}"
            f" | DisruptionMargin={disruption_margin:.4f}"
            f" | Impact={impact_score:.4f}"
            f" | ImpactMargin={impact_margin:.4f}"
            f" | Routine={routine_score:.4f}"
            f" | Final={final_score:.4f}"
        )

        logger.info(
            f"[AI FILTER] Accepted | "
            f"Final={final_score:.4f} | "
            f"Disruption={disruption_score:.4f} | "
            f"Impact={impact_score:.4f} | "
            f"Routine={routine_score:.4f}"
        )

        return {
            "accepted": True,
            "score": round(final_score, 4),
            "label": "Supply chain disruption risk",
            "reason": reason,
        }


# ==========================================================
# SINGLETON INSTANCE
# ==========================================================

relevance_filter = AIRelevanceFilter()