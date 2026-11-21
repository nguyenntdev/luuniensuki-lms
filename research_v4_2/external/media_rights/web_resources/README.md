# P07 Europeana secondary endpoint

The sample contains the normalized projections of 87 test-resource XML/RDF paths smaller than 100,000 bytes from the pinned Europeana Metis and Corelib trees. Each entry identifies its immutable raw URL. All returned HTTP 200 (623,856 bytes total). Fixtures include deliberate invalid records and variants of the same object. They establish examples of scope variation, not population frequencies.

For each distinct aggregation ID beginning with /aggregation/provider/, we requested its suffix from data.europeana.eu/item/ with Accept application/rdf+xml. endpoint.json retains all 16 outcomes. Only the Kamra record resolved. The [derived labels](labels.json) freeze the three resource declarations, retrieval URL and SHA-256 of the public RDF. Supply a local copy of the RDF to the scoring script to verify the extraction and digest.

Run python research_v4_2/external/media_rights/web_resources/score.py from the repository root. Both predictions use only the pinned fixture. Exact resource URI joins compare file declarations with aggregation declarations propagated to linked resources. The separately retrieved public RDF supplies evaluation labels. Empty declarations and unmatched URIs remain in the comparison.

Across three published resource URIs, the direct proxy matched all three declaration sets, including two empty sets. Propagation matched one empty set. The image explicitly carries In Copyright while the linked aggregation supplies CC BY-NC 3.0. The landing page has no direct declaration. The manifest has no matched fixture prediction. These are metadata declarations, not evidence of legal permission. Both representations may share upstream metadata. One object from one provider supports a worked counterexample only.
