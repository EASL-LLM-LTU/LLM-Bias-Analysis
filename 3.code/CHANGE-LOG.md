initialize.py

* Added support for an embedding column right from initialization.
* Implemented get_embedding() using Hugging Face BERT (bert-base-uncased) with mean pooling to generate vector embeddings.
* During initialization, if a row is missing an embedding, it automatically calls get_embedding() and fills it in.
* Ensures the output CSV always contains:
output_id, output, prompt_id, prompt, alpha, beta, mode, var, embedding.
* First run will download and cache Hugging Face resources:
* vocab.txt -> BERT vocabulary (~30k tokens).
* tokenizer_config.json -> tokenizer settings.
* config.json -> model architecture (hidden size, layers, etc.).
* model.safetensors -> pretrained model weights (~440 MB).


easl.py
* Parses embeddings from JSON into NumPy arrays when loading items.
* Backfills embeddings on load if they’re missing.
* Added a cosine similarity helper to measure closeness between embeddings.
* Updated getNextK():
* Iteration 0 -> random grouping to cover the full pool once.
* Later iterations -> partner selection uses both scalar match-quality (variance + mode) and embedding similarity.
* Embeddings are cached in memory to avoid repeated JSON parsing.


main.py
*	Introduced CLI flags for embeddings:
*	--emb-col -> column name (default: embedding).
*	--emb-weight -> blending weight for embeddings vs. scalars.
* --emb-eps -> floor factor to avoid zeroing out probabilities.
* Added logging after generate: shows number of items selected and how many already had embeddings.
* Added logging after update: shows ratings applied and proportion of items with >=1 rating.
