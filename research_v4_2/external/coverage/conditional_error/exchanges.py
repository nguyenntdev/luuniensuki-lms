"""Count admissions and displacements at the same accepted volume within each course."""
import csv
import gzip
from pathlib import Path
import sys
from collections import defaultdict


def main():
    with gzip.open(Path(__file__).with_name('predictions.csv.gz'), 'rt') as fp:
        course_rows = defaultdict(list)
        for row in csv.DictReader(fp):
            course_rows[row['code_module']].append(row)
    writer = csv.writer(sys.stdout, lineterminator='\n')
    writer.writerow(['course','comparator','accepted_each','retained','exchanged','errors_retained',
                     'errors_incoming','errors_displaced','difference_errors'])
    for course, rows in sorted(course_rows.items()):
        incorrect = {i for i,r in enumerate(rows) if r['prediction'] != r['final_result']}
        primary = {i for i,r in enumerate(rows) if r['conditional_accepted']=='True'}
        for name in ('confidence','negative_entropy','margin_control'):
            other = {i for i,r in enumerate(rows) if r[f'{name}_accepted']=='True'}
            assert len(primary)==len(other)==7*len(rows)//10
            retained, added, dropped = primary & other, primary-other, other-primary
            add_errors, drop_errors = len(incorrect&added), len(incorrect&dropped)
            assert add_errors-drop_errors==len(primary&incorrect)-len(other&incorrect)
            writer.writerow([course,name,len(primary),len(retained),len(added),len(incorrect&retained),
                             add_errors,drop_errors,add_errors-drop_errors])


if __name__=='__main__':
    main()
