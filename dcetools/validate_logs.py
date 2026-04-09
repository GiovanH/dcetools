

import argparse
import functools
import glob
import json
import operator
import pprint
from datetime import datetime
from typing import TypedDict

import joblib
import tqdm

memory = joblib.Memory(location='/tmp/cache')


class Record(TypedDict):
    content: str
    timestamp: str
    id: str
    author: str
    channel: str
    file: str

@memory.cache
def loaddocs(iglob):
    messages: list[Record] = []

    for input_path in tqdm.tqdm(glob.glob(iglob)):
        with open(input_path, 'r', encoding='utf-8') as fp:
            json_doc = json.load(fp)
            messages.extend([
                {
                    "content": m['content'],
                    "timestamp": m['timestamp'],
                    "id": m['id'],
                    "author": m['author']['name'],
                    "channel": json_doc['channel']['id'],
                    "file": input_path}
                for m in json_doc['messages']
            ])

    return messages

def printcompare(record: Record, ref_sorted: list, idx: int):
    pprint.pprint(record)
    for rec in [*ref_sorted[idx-3:idx], record, *ref_sorted[idx:idx+3]]:
        print(rec['id'], rec['timestamp'], rec['author'], rec['content'], rec['file'])

def all_messages(docs):
    return functools.reduce(operator.iadd, [
        [
            {**m, "channel": json_doc['channel']['id']}
            for m in json_doc['messages']
        ]
        for json_doc in docs
    ], [])

def parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts)

def validate(query_messages, baseline_messages):
    # baseline_messages: list[Message] = all_messages(baseline_docs)
    print("Baseline", len(baseline_messages))

    # query_messages: list[Message] = all_messages(query_docs)
    print("Query", len(query_messages))

    ref_sorted = sorted(baseline_messages, key=lambda x: x["id"])
    ref_ids = [r["id"] for r in ref_sorted]
    total_ids = len(ref_ids)

    for record in query_messages:
        cid = record["id"]
        cts: datetime = parse_ts(record["timestamp"])

        # Find insertion point in reference IDs
        import bisect
        pos = bisect.bisect_left(ref_ids, cid)

        # print(cid, pos)

        # Check the next lower ID (predecessor)
        if pos > 0:
            pred = ref_sorted[pos - 1]
            pts = parse_ts(pred['timestamp'])
            if not (pts < cts):
                print(f"FAIL: id={cid} timestamp {cts} not after predecessor id={pred['id']} {pts}")
                printcompare(record, ref_sorted=ref_sorted, idx=pos)
                return False
            # print(f"FAIL: id={cid} timestamp not after predecessor id={pred['id']}")

        # Check the next higher ID (successor)
        if pos < len(ref_sorted):
            # Skip if this ID exists in reference (same ID, check equality or skip)
            succ = ref_sorted[pos]
            if succ["id"] == cid:
                # Same ID exists — check timestamps match
                sts = parse_ts(succ['timestamp'])
                if sts != cts:
                    print(f"FAIL: id={cid} exists in reference but timestamps differ")
                    printcompare(record, ref_sorted=ref_sorted, idx=pos)
                    return False
            else:
                sts = parse_ts(ts=succ['timestamp'])
                if not (cts < sts):
                    print(f"FAIL: id={cid} timestamp not before successor id={succ['id']}")
                    printcompare(record, ref_sorted=ref_sorted, idx=pos)
                    return False

        print(cid, pos, total_ids, cts)

    print("Done")
    return True

def main(args):
    print(args)

    query_docs = loaddocs(args.query_glob)
    print("Loaded")
    baseline_docs = loaddocs(args.baseline_glob)
    print("Loaded")

    validate(query_docs, baseline_docs)
    print("Validated")


def define_parser(parser: argparse.ArgumentParser):
    parser.description = "Validate a set of unknown discord logs against a set of known logs. This looks for signs of tampering, namely out-of-order messages."
    parser.add_argument('query_glob', help='Input json files')
    parser.add_argument('baseline_glob', help='Input json files')
    parser.set_defaults(func=main)

    return parser

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="()",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    define_parser(parser)
    args = parser.parse_args()
    args.func(args)
