# What a museum catalogue can tell a reuser about image rights

## Abstract

An image locator identified 41,869 Cleveland Museum of Art records labelled CC0 and zero labelled Copyrighted. The same rule identified 59,063 Art Institute of Chicago records marked public domain and 64,698 whose public-domain flag was false. Requiring both a locator and a blank copyright notice still selected 52,202 Chicago records with a false flag. These counts measure disagreement with the museums’ object-level declarations. Two further collections illustrate why the scope of those declarations matters. Tate excludes images from its catalogue licence, while the Smithsonian supplies individual image declarations.

## Design and comparators

Kristin Kelly documented how eleven American and British art museums managed images of public-domain works. Andrea Wallace surveyed UK cultural institutions and documented variation within as well as across institutions. We test a specific consequence for catalogue users. Does an image locator carry the same predictive value when an automated client moves between museum exports? [Kelly, *Images of Works of Art in Museum Collections*](https://www.clir.org/pubs/reports/pub157/) · [Wallace, *A Culture of Copyright*](https://doi.org/10.2139/ssrn.4323683)

We use all artwork rows from Cleveland’s pinned CSV and all artwork objects from Chicago’s October 2026 bulk API release. Each museum supplies its own reference label. Cleveland’s positive class is `share_license_status=CC0` and its negative class is `Copyrighted`. Chicago’s classes are the two values of `is_public_domain`. Chicago defines this as a property of the work and defines `image_id` as an identifier for a preferred image. Its `copyright_notice` also concerns the work. Cleveland publishes a web-image URL when applicable. A URL and a preferred-image identifier both let a client construct an image request, though neither proves that the request will succeed. We preserve the two label meanings and denominators. [Chicago field definitions](https://github.com/art-institute-of-chicago/data-aggregator/blob/722ac849ce4a1fac3115b4bcf587c72d6ac778ab/app/Transformers/Outbound/Collections/Artwork.php) · [Chicago bulk release documentation](https://github.com/art-institute-of-chicago/api-data/tree/8c7e65089ac8145a241f237e065c81861a35f359) · [Cleveland release documentation](https://github.com/ClevelandMuseumArt/openaccess/blob/e75f7fbcb5c3dab41c40917f3a6ce4e411904b7a/README.md)

Each rule sees only the presence of an image locator and/or a nonblank copyright notice (Cleveland `image_web` and `copyright`, Chicago `image_id` and `copyright_notice`). We score both constant decisions as controls. Every rule runs on exactly the same rows within each museum, including works without a locator. No rule reads the reference label, fits parameters, or uses one museum to set a threshold for the other. The publishers may derive several fields from the same internal workflow, so even perfect agreement would only describe that export. Tate and Smithsonian remain scope checks because their available evidence does not supply comparable mixed object labels.

## Results

| Source and unit | Observable evidence | Decision supported |
|---|---|---|
| Tate, 69,201 artwork records | 58,415 had a thumbnail URL. Of these, 14,239 had a copyright notice and 44,176 did not. | Inheriting CC0 would promote all 58,415 links. Requiring an empty notice would still promote 44,176. The catalogue licence supplies an image grant for neither group. |
| Smithsonian, 103 records in FSG shards 00–05 | 179 media entries had type Images and a nonempty content locator. All 179 had usage.access equal to CC0. | The publisher supplied an explicit media-level declaration for every qualifying entry sampled. |
| Cleveland, 68,819 catalogue records | Of 42,637 labelled CC0, 41,869 had a web image and 768 did not. All 26,182 labelled Copyrighted lacked a web image. | Inheriting dataset CC0 for every object disagrees with the publisher’s status on 26,182. A web-link proxy for CC0 misses 768 CC0 objects. |

### Cross-provider transfer

Cleveland has 42,637 positive and 26,182 negative records. Chicago has 62,119 positive and 77,633 negative records. A false positive selects a negative record. A false negative misses a positive record.

| Select a record when… | Cleveland false positives | Cleveland false negatives | Chicago false positives | Chicago false negatives |
|---|---:|---:|---:|---:|
| Always | 26,182 | 0 | 77,633 | 0 |
| Never | 0 | 42,637 | 0 | 62,119 |
| Image locator present | 0 | 768 | 64,698 | 3,056 |
| Copyright notice blank | 17,528 | 0 | 64,458 | 0 |
| Locator present and notice blank | 0 | 768 | 52,202 | 3,056 |

The locator rule’s false-positive rate rose from 0% at Cleveland to 83.34% at Chicago, measured against each provider’s negative class. Requiring a blank notice reduced Chicago’s rate to 67.24%, with the same 3,056 missed positive records. For a record-level check, Chicago artwork 247 has an image identifier, a blank notice and a false public-domain flag. Artwork 45 has a true flag and no preferred-image identifier. Those two cases illustrate both directions of error without interpreting the rights to either image. [Frozen object-level inputs](objects.csv.gz) · [Joint counts and complete confusion matrices](transfer.json)

Tate expressly limits the scope of its dataset licence to metadata. A thumbnail URL supports navigation and a blank notice records no affirmative grant. These observations cannot determine how many individual images are actually in the public domain or separately licensable. The Smithsonian schema offers more direct evidence through each image entry. Because every qualifying entry in the six shards was marked CC0, a rule that approves every link yields the same decisions on this subset. It provides no negative examples with which to test a rights classifier. [Tate’s scope statement](https://github.com/tategallery/collection#the-tate-collection) · [Smithsonian Open Access](https://github.com/Smithsonian/OpenAccess) · [Tate and Smithsonian counts](result.json)

Cleveland supplies a stronger control because its dataset includes both publisher statuses and its documentation describes the image assets covered by open access. For identifying *publisher-labelled CC0 objects*, a web URL proxy has 41,869 matches, zero false positives and 768 false negatives in this export. For locating *available web images on CC0 objects*, those 768 records provide no web-image URL. Conflating these targets would misstate the baseline’s errors. [Cleveland’s release documentation](https://github.com/ClevelandMuseumArt/openaccess/blob/e75f7fbcb5c3dab41c40917f3a6ce4e411904b7a/README.md) · [Cleveland cross-tabulation](cleveland.json)

## Can another record supply a withheld declaration?

We masked flags on 100,875 Met development objects while retaining 302,046 labelled training objects. A model using nearby accession or artist records cleared the initial .005-nat log-loss margin against three controls. A follow-up supplied a stronger control that could use nearby labels along the inventory ID alone. It achieved .13728 nats versus .13778 for the full grouped model. The subsequent rich-metadata comparison also favoured a simple two-order donor model. An audit of actual historical Minneapolis declarations found no later fills among 17 initially blank training records. The observed development advantage on randomly masked objects therefore does not establish effectiveness on the museum's unresolved cases. [Met methods and evidence](imputation/README.md) · [Historical Minneapolis audit](imputation/transfer/README.md)

## Limits

Each source uses a different unit. Tate and Cleveland report object rows, while a Smithsonian record can carry several images. The six Smithsonian shards are a prefix of one collecting unit’s export. They provide neither a random sample of the institution nor an estimate of restricted-media prevalence. Cleveland’s object-level status is a publisher label, distinct from an independent legal determination for every rendition. This audit did not fetch image bytes, test link availability, determine jurisdiction-specific rights, or consult separate licences. The Chicago export and Cleveland CSV are separate snapshots. Their difference cannot establish a change over time or isolate the effects of institutional policy from collection composition. Pooling the three denominators would conceal these differences.

## Reproduction

From the repository root, run the following in Bash with curl and Python 3.12. The following commands check the counts and source hashes. For an offline replay of the mixed-label comparison, run the last scoring command against the included projection. The Smithsonian S3 keys are mutable. If the first diff reports a changed shard hash, use the hash-matching archived copy under private_data/raw/smithsonian_open_access/2021-12-21 when available. Cleveland’s download uses Git LFS media delivery to fetch the CSV bytes.

```bash
set -euo pipefail
work=$(mktemp -d)
paper=research_v4_2/external/media_rights
si="$work/smithsonian_open_access/2021-12-21"
mkdir -p "$work/tate" "$si"
tate=https://raw.githubusercontent.com/tategallery/collection/e7936a63d954d5b17628c59990531d723d2da010
curl -fsSL "$tate/artwork_data.csv" -o "$work/tate/artwork_data.csv"
base=https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/fsg
for shard in 00 01 02 03 04 05; do
  curl -fsSL "$base/$shard.txt" -o "$si/fsg_$shard.txt"
done
python "$paper/evaluate.py" "$work" | diff - "$paper/result.json"
cma=https://media.githubusercontent.com/media/ClevelandMuseumArt/openaccess/e75f7fbcb5c3dab41c40917f3a6ce4e411904b7a
curl -fsSL "$cma/data.csv" -o "$work/cleveland.csv"
python "$paper/cleveland.py" "$work/cleveland.csv" | diff - "$paper/cleveland.json"
curl -fsSL --retry 3 https://artic-api-data.s3.amazonaws.com/artic-api-data.tar.bz2 -o "$work/chicago.tar.bz2"
python "$paper/transfer.py" build "$work/cleveland.csv" "$work/chicago.tar.bz2" "$work/objects.csv.gz"
python "$paper/transfer.py" score "$work/objects.csv.gz" | diff - "$paper/transfer.json"
python "$paper/transfer.py" score "$paper/objects.csv.gz" | diff - "$paper/transfer.json"
```

Chicago refreshes its bulk archive. The build checks both raw hashes before extraction. The frozen projection retains provider, object ID and three binary fields, sufficient to replay every comparison after a refresh. Scoring checks the decompressed projection hash so that different gzip implementations can produce equivalent inputs.
