# Token efficiency

The model sees a handful of chunks, not the guideline corpus.

## Why a large context hurts

A long prompt costs more, returns later, and gives the model more untrusted text to follow. Chunks that are only loosely related compete with the two or three rules that matter. The Harbor conflict is the example: both revenue rules need to be in the window, and the injection chunk does not.

## What this slice sends

The search tool retrieves at most `retrieval_k` chunks (default 5). Metadata filters drop chunks whose industry, product, or countries disagree with the submission. The draft prompt then contains structured facts, the narrative, and those chunks. Citation headers are added by the application. The evaluation command prints the mock's prompt-token estimate so a prompt edit has a number next to it.

The mock estimate counts the text it was given. It is not the provider tokenizer. It is stable enough to notice a change that pastes the corpus back in.

## Retrieval strategy

The query is built from industry, countries, product, and a few fixed underwriting words. It is not built from the narrative, so a long or hostile narrative does not steer retrieval. The lexical ranker misses paraphrases. Those misses are the soft cases in the golden set. A vector retriever is the same port with a different scorer, still capped at k.

## Caching

This demo does not cache model responses. A safe cache key would be the submission fingerprint plus the ids and hashes of the retrieved chunks, not the narrative alone. Caching a draft across users would be wrong: the same company can sit on two submissions with different assignees, and the cache would have to keep the caller's scope out of the key by never storing another user's draft under it. Guideline chunks change rarely and are the better cache: the ranker already holds them in memory for the process.
