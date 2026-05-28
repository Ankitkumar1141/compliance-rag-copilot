"""
ragas_eval.py

Evaluates the RAG pipeline using RAGAS metrics:
- Faithfulness
- Answer Relevancy
- Context Recall
- Context Precision

Requires: pip install ragas
"""

import os
import json
from typing import List, Dict, Optional

from dotenv import load_dotenv
load_dotenv()


def run_ragas_evaluation(
    questions: List[str],
    answers: List[str],
    contexts: List[List[str]],
    ground_truths: List[List[str]],
) -> Optional[Dict]:
    """
    Runs RAGAS evaluation on a set of Q&A pairs with retrieved context.

    Args:
        questions: List of user queries.
        answers: List of generated answers (from the RAG pipeline).
        contexts: List of lists — for each query, the retrieved context chunks.
        ground_truths: List of lists — for each query, the expected ground truth answers.

    Returns:
        Dict with RAGAS metric scores, or None if RAGAS is unavailable.
    """
    try:
        from ragas import evaluate
        from ragas.metrics import (
            faithfulness,
            answer_relevancy,
            context_recall,
            context_precision,
        )
        from datasets import Dataset
    except ImportError:
        print(
            "[WARNING] RAGAS or datasets library is not installed. "
            "Run: pip install ragas datasets\n"
            "Skipping RAGAS evaluation."
        )
        return None

    if not (len(questions) == len(answers) == len(contexts) == len(ground_truths)):
        raise ValueError("All input lists must have the same length.")

    # Build HuggingFace Dataset required by RAGAS
    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truths": ground_truths,
    }
    dataset = Dataset.from_dict(data)

    print(f"[INFO] Running RAGAS evaluation on {len(questions)} samples...")

    try:
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        )
        scores = result.to_pandas().mean(numeric_only=True).to_dict()
        print("[INFO] RAGAS Evaluation Results:")
        for metric, score in scores.items():
            print(f"  {metric}: {score:.4f}")
        return scores
    except Exception as e:
        print(f"[ERROR] RAGAS evaluation failed: {e}")
        return None


def run_benchmark_evaluation(pipeline_fn) -> Optional[Dict]:
    """
    Runs RAGAS evaluation using the built-in benchmark dataset.

    Args:
        pipeline_fn: A callable that takes a query string and returns
                     {"answer": str, "sources": list, "context_docs": list}
    """
    from rag.evaluation.benchmark_dataset import get_benchmark_dataset

    benchmark = get_benchmark_dataset()

    questions, answers, contexts, ground_truths = [], [], [], []

    for item in benchmark:
        query = item["question"]
        expected = item["ground_truth"]

        try:
            result = pipeline_fn(query)
            answer = result.get("answer", "")
            docs = result.get("context_docs", [])
            context_texts = [doc.page_content for doc in docs] if docs else [""]
        except Exception as e:
            print(f"[ERROR] Pipeline failed for query '{query[:60]}': {e}")
            answer = ""
            context_texts = [""]

        questions.append(query)
        answers.append(answer)
        contexts.append(context_texts)
        ground_truths.append([expected])

    return run_ragas_evaluation(questions, answers, contexts, ground_truths)


if __name__ == "__main__":
    # Example: run evaluation against the mock pipeline
    print("[INFO] Running benchmark evaluation with mock pipeline...")
    from models.llm_factory import MockChatModel

    def mock_pipeline(query: str) -> Dict:
        """Minimal mock to test the evaluation harness."""
        return {
            "answer": "Based on compliance documentation, plain text password storage is prohibited.",
            "sources": [],
            "context_docs": [],
        }

    scores = run_benchmark_evaluation(mock_pipeline)
    if scores:
        output_path = "data/processed_docs/ragas_results.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(scores, f, indent=2)
        print(f"[INFO] Saved RAGAS scores to: {output_path}")
