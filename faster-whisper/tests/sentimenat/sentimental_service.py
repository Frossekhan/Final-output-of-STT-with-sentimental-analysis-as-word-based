from transformers import pipeline

class SentimentService:

    def __init__(self):
        self.classifier = pipeline(
            "sentiment-analysis"
        )

    def analyze(self, text):

        result = self.classifier(text)

        return {
            "label": result[0]["label"],
            "score": round(result[0]["score"], 4)
        }