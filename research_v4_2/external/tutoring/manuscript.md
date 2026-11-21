# A fixed tutor outscored four published guidance-grader configurations on MRBench response selection

Across 300 archived mathematics conversations, selecting the tutor with the highest training guidance rate yielded **238 fully guiding responses (79.3%)**. A lexical selector with tutor identity yielded 224. Four locally refitted configurations from the DLSU BEA 2025 system yielded 198–209. In 291 conversations at least one of the six candidates earned the full guidance label. Thus an ideal selector could have recovered 53 fixed-policy misses. Even the best-performing published configuration in this comparison lost more fixed-policy successes than it recovered.

## Question and prior work

Maurya et al. introduced a taxonomy for assessing tutor responses to student mistakes. The BEA shared task evaluated predictions of individual pedagogical labels. DLSU compared frozen response embeddings coupled with an MLP or XGBoost and submitted its two GTE configurations for the official guidance track. We ask a different decision question using the same rubric. When six responses are available for a conversation, does choosing the grader’s highest-scoring response improve on always choosing the strongest tutor seen in training? A grader can correctly rank many pairs and still switch away from a good default too often. The contribution here is a paired evaluation of those switches with a measured upper bound. [MRBench taxonomy](https://aclanthology.org/2025.naacl-long.57/) · [Shared-task findings](https://aclanthology.org/2025.bea-1.77/) · [DLSU system](https://aclanthology.org/2025.bea-1.101/)

## Data and evaluation

Use the 300 labeled conversations in the shared-task development release. Each offers responses from the same six language-model tutors. Success requires the released Providing_Guidance label “Yes”. The graders learn all three published label classes and rank responses by the probability of “Yes”. The lexical models learn the binary selection endpoint. No grader sees the dialogue history or the reference solution. The expert response is outside the six-way choice. The 191 official test records have no released annotations and contribute zero scored outcomes. [Pinned source archive](https://github.com/kaushal0494/UnifyingAITutorEvaluation/tree/bbef521ddb875f2cc8a5ee798f4066965a7cfd8a)

The original split trained on 192 conversations and tuned on 56, leaving 52 for evaluation. We extended that analysis by rotating the same five disjoint opening-prompt buckets. Three buckets supply training data and one supplies tuning data for each test bucket. This yields one held-out decision per conversation across 206 groups. Each of the five training samples selected Llama-3.1-405B as its unique best fixed tutor. The DLSU reproductions use published Track 3 hyperparameters with local classifier fits. Six of seven MiniLM MLP fits reached the 1000-iteration cap. DLSU tuned its published settings on the shared development archive, so the local holdouts cannot establish independent external validation. [Fitting and reproduction protocol](protocol.md)

## What the policies selected

“Recovered” counts conversations where the policy alone succeeded relative to the fixed tutor. “Lost” counts conversations where the fixed tutor alone succeeded. Differences and opening-group bootstrap intervals are in percentage points. The 52-case holdout is included in the 300-case column.

| Policy | Original holdout / 52 | Five folds / 300 | Recovered | Lost | Difference vs fixed, 95% interval |
|---|---:|---:|---:|---:|---:|
| Tutor identity only | 46 | 238 | – | – | Reference |
| Response words only | 34 | 216 | 22 | 44 | −7.3 [−12.4, −2.3] |
| Tutor identity and response words | 38 | 224 | 18 | 32 | −4.7 [−9.2, −0.3] |
| DLSU MiniLM + MLP | 37 | 208 | 31 | 61 | −10.0 [−16.5, −3.7] |
| DLSU MiniLM + XGBoost | 39 | 201 | 23 | 60 | −12.3 [−18.3, −6.7] |
| DLSU GTE + MLP | 33 | 198 | 23 | 63 | −13.3 [−19.5, −7.5] |
| DLSU GTE + XGBoost | 38 | 209 | 23 | 52 | −9.7 [−15.7, −4.1] |
| Oracle using released labels | 50 | 291 | 53 | 0 | +17.7 ceiling |

Adding the tutor token improved lexical selection by eight successes pooled across folds. The identity-only policy still exceeded the combined selector by 14. In the original holdout the combined selector recovered one fixed-policy failure and lost nine successes. Expert responses earned “Yes” in 33 of those 52 cases. This single rubric dimension measures one property of the archived responses.

The ceiling distinguishes three kinds of conversation. Nine had no fully guiding candidate, 48 had six, and 243 had a mix. Only those 243 allowed a selection policy to change the outcome. GTE + XGBoost recovered 23 of 53 available fixed-policy misses (43%), but traded away 52 of the fixed policy’s 238 successes. The original holdout offered only four recoverable misses. The larger opportunity estimate comes from evaluating all five folds. [All candidate scores and labels](run/grader_scores.csv) · [Fold summaries and oracle counts](run/comparison.json)

## Transfer between dialogue sources

MRBench V2 supplied source metadata for 182 V3 records matched by both conversation ID and normalized full history. No V2 conversation survived exclusion of all V3 IDs and opening groups as an independent transfer case. Instead we fitted on one linked source and evaluated on the other. These are two source subsets of MRBench, sampled under a common annotation protocol. [V2 archive](https://github.com/kaushal0494/UnifyingAITutorEvaluation/blob/bbef521ddb875f2cc8a5ee798f4066965a7cfd8a/MRBench/MRBench_V2.json)

| Fitting → evaluation source | Train / tune / test cases | Fixed | Words | Identity + words | MiniLM MLP / XGB | GTE MLP / XGB | Oracle |
|---|---:|---:|---:|---:|---:|---:|---:|
| MathDial → Bridge | 117 / 28 / 37 | 30 | 28 | 27 | 25 / 26 | 31 / 26 | 37 |
| Bridge → MathDial | 31 / 6 / 145 | 71 | 83 | 93 | 83 / 90 | 88 / 89 | 141 |

On Bridge, GTE + MLP gained one success over the fixed tutor. Its paired interval spanned −10.8 to +16.2 points. In the reverse direction the fixed tutor’s identity depended on the tie rule. Gemini and Llama-3.1-405B each scored 25/31 in Bridge training. Alphabetical order selected Gemini, which scored 71/145 on MathDial. Choosing the equally qualified Llama instead would have scored 111/145 and reversed every adaptive policy’s apparent advantage. The small origin sample cannot resolve that choice.

These results concern offline selection among already-generated responses to mathematics conversations. The experiment measures neither the effect of a response on learning nor the quality of deployment-time generation. The paired intervals condition on the fitted selectors. All comparisons reuse one released annotation archive. [Original decisions](run/decisions.csv) · [Extended evaluator](compare.py) · [Reproduction instructions](protocol.md)

## External evaluation on expert revisions of novice responses

The IndoML Datathon training release repeats the histories of the 300 scored MRBench development cases. The 41 development-test and 150 test histories all occur in the official MRBench test release, and their response records contain no annotations. A different release, MathTutorBench, supplies 482 Bridge pairs in which an expert revised a novice teacher's response. This affords a second endpoint: can a reader with the two unlabelled response texts select the expert revision? The expert role itself identifies the preferred response when roles are visible. [Macina et al., EMNLP 2025](https://aclanthology.org/2025.emnlp-main.11/) · [Overlap verifier](bridge/verify.mjs)

The initial protocol required disjoint problem strings. Every released Bridge test row had a blank problem field, leaving zero eligible pairs. Before fitting or computing scores we fixed a secondary topic-level design. We trained on the 8,136 released training pairs. Applying the disjointness checks excluded 20 shared dialogues and then 38 additional pairs with a shared response. The evaluation retained 424 pairs across 154 topics. Literal overlap filtering cannot rule out paraphrased variants of the same problem. [Initial protocol](bridge/protocol.md) · [Secondary protocol](bridge/topic_protocol.md)

The joint word- and character-based ranker selected the expert response in 360 of 424 pairs (84.9%). The word-only ranker also selected 360: adding character features gained 16 successes and lost 16. The paired gain was 0.0 percentage points (simultaneous 95% interval −3.91 to +3.79, resampling topics). The character-only model selected 348, the longer response 172, the response with more questions 307, and lexicographic first 303. The known-role rule selected all 424 by construction. The word-only tie triggered the prespecified stop before the EMNLP reward-model comparison. The result concerns recognition of an editorial choice; student learning and the relative quality of identified generative tutors require different evidence. [All decisions](bridge/topic_run/decisions.csv) · [Results](bridge/topic_run/result.json) · [Reproduction](bridge/README.md)

### Joint success across four rubric dimensions

Choosing the fixed tutor on MathDial using four rubric dimensions changed the selected tutor from GPT4 to Llama31405B. The number of Bridge conversations meeting all four criteria increased from 6 to 19 out of 37. Both training objectives selected Gemini in the reverse direction and it met the joint criterion on 58 of 145 conversations. This asymmetry limits transfer claims based on optimizing the guidance label alone. [Criteria, source splits and paired intervals](multiple_rubrics/README.md)
