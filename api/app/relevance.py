# cosine distance cutoff for "actually relevant" - measured empirically
# against nomic-embed-text: on-topic pairs land ~0.3-0.4, off-topic pairs
# ~0.6+. Without this, a top-K query with few notes/chunks in the account
# surfaces unrelated content as "relevant" just because nothing better exists.
MAX_RELEVANT_DISTANCE = 0.5
