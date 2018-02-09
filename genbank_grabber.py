#!/usr/bin/env python

import argparse
import logging
import os
import requests
import sys


class genbank_api(object):
    def __init__(self, genbank_id, filename="", outdir="fasta"):
        # url definitions
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.search_url = "/esearch.fcgi?db=nuccore&term={id}&usehistory=y"
        self.fetch_url = "/efetch.fcgi?db=nuccore&query_key={query_key}&WebEnv={webenv}"
        self.ret_params = "&rettype=fasta&retmode=text"
        # record specific information
        self.genbank_id = genbank_id
        self.query_key = ""
        self.webenv = ""
        self._raw_results = ""
        self.fasta = ""
        self.fasta_name = ""
        self.filename = filename
        self.outdir = outdir

    def _construct_url(self, query_type, return_type="fasta"):
        url = ""
        if query_type == "search":
            url = self.base_url + self.search_url.format(id=self.genbank_id)
        elif query_type == "fetch":
            if len(self.query_key) > 0 and len(self.webenv) > 0:
                url = self.base_url + self.fetch_url.format(query_key=self.query_key, webenv=self.webenv)
                if return_type == "fasta":
                    url += self.ret_params
                else:
                    raise ValueError("Fetch only supports fasta for now")
            else:
                raise ValueError("A search query must be run before a fetch query")
        return url

    def search(self):
        url = self._construct_url("search")
        r = str(requests.get(url).content)
        # save raw results just in case
        self._raw_results = r

        query_key_index = r.index("<QueryKey>") + len("<QueryKey>")
        self.query_key = r[query_key_index:query_key_index + 1]
        webenv_index_begin = r.index("<WebEnv>") + len("<WebEnv>")
        webenv_index_end = r.index("</WebEnv>")
        self.webenv = r[webenv_index_begin:webenv_index_end]

        return None

    def fetch(self):
        if len(self.query_key) == 0 or len(self.webenv) == 0:
            self.search()
        url = self._construct_url("fetch")
        r = requests.get(url)
        self.fasta = r.content.decode()
        self.fasta_name = self.fasta.split("\n")[0]
        return None

    def save_fasta(self):
        self._create_output_dir()
        if len(self.fasta) == 0:
            self.fetch()
        if len(self.filename) > 0:
            cur_dir = os.path.abspath(os.curdir)
            with open(os.path.join(cur_dir, self.outdir, self.filename), 'w') as f:
                f.write(self.fasta)
        else:
            sys.stdout.write(self.fasta)
        return None

    def _create_output_dir(self):
        if not os.path.exists(self.outdir):
            os.mkdir(self.outdir)
        else:
            pass
        return None


def main(args, loglevel):
    logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)
    gb = genbank_api(args.genbank_id, args.out)
    gb.save_fasta()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Downloads fasta sequence of a genbank ID",
        epilog="This is the epilog")
    # TODO Specify your real parameters here.
    parser.add_argument(
        "genbank_id",
        help="genbank ID to download",
        metavar="genbank_ID",
        default=sys.stdin)
    parser.add_argument(
        "-o",
        "--out",
        help="output filename, default: stdout",
        default="")
    parser.add_argument(
        "-v",
        "--verbose",
        help="increase output verbosity",
        action="store_true")

    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    main(args, loglevel)
