"""
NLTK setup utilities for looksatwords package.
"""


def ensure_nltk_data():
    """Download required NLTK data if not already present."""
    import nltk
    
    required_datasets = [
        'punkt_tab',
        'averaged_perceptron_tagger_eng', 
        'stopwords',
        'wordnet',
        'vader_lexicon'
    ]
    
    missing_datasets = []
    
    # Check which datasets are missing
    for dataset in required_datasets:
        try:
            # Try different possible locations for each dataset
            for location in ['tokenizers', 'taggers', 'corpora', 'sentiment']:
                try:
                    nltk.data.find(f'{location}/{dataset}')
                    break
                except LookupError:
                    continue
            else:
                missing_datasets.append(dataset)
        except Exception:
            missing_datasets.append(dataset)
    
    # Download missing datasets
    if missing_datasets:
        try:
            for dataset in missing_datasets:
                nltk.download(dataset, quiet=True)
            print(f"Installed NLTK packages: {', '.join(missing_datasets)}")
        except Exception as e:
            print(f"Error installing NLTK packages: {e}")


if __name__ == "__main__":
    ensure_nltk_data()