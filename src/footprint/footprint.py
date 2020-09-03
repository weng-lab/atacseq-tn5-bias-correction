#!/usr/bin/env python

import sys
import argparse

from typing import List, Tuple
from pysam import Fastafile, Samfile

from rgt.Util import ErrorHandler, HmmData, GenomeData, OverlapType
from rgt.HINT.signalProcessing import GenomicSignal
from rgt.HINT.biasTable import BiasTable

from .constants import *

def expandRegion(chromosome, start, end, w = 500):
    m = int((int(start) + int(end)) / 2)
    return chromosome, m - w, m + w

def regionDict(k, forward, reverse):
    chromosome, start, end = k
    return {
        "chromosome": chromosome,
        "start": start,
        "end": end,
        "forward": forward,
        "reverse": reverse
    }

def footprint(bam: str, bed: str, assembly: str = "hg38", w: int = 500):

    # load HMM and bias parameters for ATAC-seq
    g = GenomeData(organism = assembly)
    hmm_data = HmmData()
    hmm_file = hmm_data.get_default_hmm_atac_paired()
    table_F = hmm_data.get_default_bias_table_F_ATAC()
    table_R = hmm_data.get_default_bias_table_R_ATAC()
    bias_table = BiasTable().load_table(table_file_name_F = table_F, table_file_name_R = table_R)

    # load reads from BAM
    reads_file = GenomicSignal(bam)
    reads_file.load_sg_coefs(SG_WINDOW_SIZE)

    # open data and sequence
    bam = Samfile(bam, "rb")
    fasta = Fastafile(g.get_genome())

    # load and expand regions
    with open(bed, 'r') as f:
        regions = [ expandRegion(*tuple(line.strip().split()[:3]), w) for line in f ]
    
    # load signal
    forward = []; reverse = []
    for i, x in enumerate(regions):
        chromosome, start, end = x
        atac_norm_f, atac_slope_f, atac_norm_r, atac_slope_r = reads_file.get_signal_atac(
            chromosome, start, end, 0, 0, FORWARD_SHIFT, REVERSE_SHIFT,
            50, 98, 98, bias_table, g.get_genome()
        )
        forward.append(atac_norm_f)
        reverse.append(atac_norm_r)

    return [ regionDict(regions[i], forward[i], reverse[i]) for i in range(len(regions)) ]
