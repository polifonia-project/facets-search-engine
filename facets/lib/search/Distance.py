import numpy as np
import math
from fractions import Fraction
# import the logging library
import logging
from django.conf import settings

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Distance:
 
    def __init__(self, alphabet=None):
        return


    @staticmethod
    def rhythmic_distance(s1, s2):
        """
        Rhythmic distance based on blocks for ranking of chromatic and diatonic search result. 

        The input consists of two sequence
        that share the same "melodic" profile: we know that the sucession of intervals is the same.
        The functions cuts each sequence in blocks of constant-pitch notes. Two successive
        blocks correspond to distinct pitches, and, as explained, the intervals between
        blocks in both sequences are pairwise equal.
        Therefore we measure the rythmic distance for each pair of block, and cumulate them."""

        # Sanity check
        if len(s1.items) == 0 or len(s2.items) == 0:
            print("Skip measurement of rhythmic distance between the current match and search pattern: one of the sequence is empty.")
            return 1000000 # Find sth cleaner
        
        # Compute blocks ranges
        blocks1 = Distance.find_blocks_range(s1)
        blocks2 = Distance.find_blocks_range(s2)

        # Check if the number of block are the same, if not raises an error
        if len(blocks1) != len(blocks2):
            print("note: this occurrence has different numbers of blocks")

        blocks1  = Distance.normalize_block_duration(blocks1)
        blocks2  = Distance.normalize_block_duration(blocks2)
        
        cost_alignment = 0
        if len(blocks1) > len(blocks2):
            shorter = len(blocks2)
            for iblock in range(shorter, len(blocks1)):
                cost_alignment += blocks1[iblock]["duration"]
        else:
            shorter = len(blocks1)
            for iblock in range(shorter, len(blocks2)):
                cost_alignment += blocks2[iblock]["duration"]

        for iblock in range(shorter):
            block1 = blocks1[iblock]
            block2 = blocks2[iblock]
            
            logger.info("Block " + str(iblock) + ". Seq1: [" + str(block1["start_pos"]) + "," + str(block1["end_pos"]) + 
                "] duration " + str(block1["duration"])
                                    + " Seq2 [" + str(block2["start_pos"]) + "," + str(block2["end_pos"]) + 
                "] duration " + str(block2["duration"]))
            
            # The sum of the normalized durations gaps represents the cost of aligning the 
            # two sequences of durations
            cost_alignment += abs(block1["duration"] - block2["duration"])
            
            # We can even do better by taking account of the internal rhythm of each block. 
            # An approximation is simply to compare the number of events in each block

            #
            # What is the rhythmic ratio between the duration of two successive blocks (Not useful??)
            #if iblock < len(blocks1) - 1:
            #    ratio1 = block1["duration"] /  blocks1[iblock+1]["duration"]
            #    ratio2 = block2["duration"] /  blocks2[iblock+1]["duration"]
            #    # print ("Ratio 1 " + str(ratio1) + " ratio 2 " + str(ratio2))
        
        return cost_alignment

    @staticmethod
    def melodic_distance(s1, s2):
        '''
            We measure melodic distance for ranking of rhythmic search, using Levenshtein distance.

            Given two sequences(the query and the current match) of pitch intervals as melodic information,
            the distance between two blocks should be the number of notes that has different pitch intervals.

            Note: pitch intervals here refers to DIATONIC INTERVALS, not semitones.
        '''
       
        blocks1 = Distance.simplified_interval_for_blocks(s1)
        blocks2 = Distance.simplified_interval_for_blocks(s2)

        # Check if the query pattern and the matched pattern has same amount of blocks
        if len(blocks1) != len(blocks2):
            print("note: this occurrence has different number of blocks compared to the search pattern")
        
        intervals_blocks1 = []
        intervals_blocks2 = []

        # In case the current two sequences don't have same numbers of blocks 

        for iblock in range(len(blocks1)):            
            block1 = blocks1[iblock]
            
            """
            # change of code, no longer needed
            logger.info("Block " + str(iblock) + ". Seq1: [" + str(block1["start_pos"]) + "," + str(block1["end_pos"]) + 
                "] diatonic interval " + str(block1["value"])
                                    + " Seq2 [" + str(block2["start_pos"]) + "," + str(block2["end_pos"]) + 
                "] diatonic interval " + str(block2["value"]))
            """
            intervals_blocks1.append(block1["value"])

        for iblock in range(len(blocks2)):
            block2 = blocks2[iblock]
            intervals_blocks2.append(block2["value"])

        # Measure the levenshtein distance between the match and the query
        cost_alignment = Distance.distance_levenshtein_for_blocks(intervals_blocks1, intervals_blocks2)
        
        return cost_alignment

    @staticmethod
    def simplified_interval_for_blocks(s):

        blocks_with_m_intervals = []

        m = s.get_intervals(settings.DIATONIC_DESCR)

        for dia_interval in m:
            # Get diatonic interval, such as "2D" representing for a descending second
            m21_interval = dia_interval["value"]
            if m21_interval[-1] == 'D':
                # Descending as a negative number
                curr_interval = -int(m21_interval[:-1])
            elif m21_interval[-1] == 'A':
                curr_interval = int(m21_interval[:-1])
            else:
                raise ValueError("Wrong format for m21_interval encoding")

            # If we change the diatonic intervals into integers, simply use the following commented line of code:
            # blocks_with_m_intervals.append({"start_pos": dia_interval["start_pos"], "end_pos": dia_interval["end_pos"], "value": curr_interval})

            blocks_with_m_intervals.append({"start_pos": dia_interval["start_pos"], "end_pos": dia_interval["end_pos"], "value": m21_interval})
        
        return blocks_with_m_intervals
    

    @staticmethod
    def find_blocks_range(s):
        """
            Take a sequence and compute the ranges of 'blocks', 
            where a block is a sequence if similar pitches.
        """
        start_current_block = 0
        block_ranges = []
        current_pos = 0
        block_duration = 0
        for item in s.items:
            # compare the pitch of current block and the pitch of current item,
            if item.get_index() != s.items[start_current_block].get_index():
                # when there's pitch changes, it's considered as a new block
                block_ranges.append({"start_pos": start_current_block, "end_pos": current_pos-1, "duration": block_duration})
                start_current_block = current_pos
                block_duration = 0
            current_pos = current_pos+1
            block_duration += item.duration
        block_ranges.append({"start_pos": start_current_block, "end_pos": len(s.items), "duration": block_duration})

        return block_ranges

    @staticmethod
    def normalize_block_duration(blocks):
        """
            Normalize the duration of a sequence of blocks
        """

        full_duration = 0
        for block in blocks:
            full_duration += block["duration"]
        for block in blocks:
             block["duration"] = block["duration"] / full_duration
        
        return blocks

    @staticmethod
    def distance_levenshtein_for_blocks(s1, s2):
        #   Compute Levenshtein distance between two sequences
        #   s1 is the occurrence, s2 is the pattern in search

        m = len(s1)
        n = len(s2)
        
        # Check if 2 sequences have difference numbers of blocks:
        # if yes, cost of deletion is the length difference
        if m != n:
            #print("s1 and s2 has different numbers of blocks:")
            #print("s1:", s1, "   / s2: ", s2)
            if m > n:
                shorter = n
            else:
                shorter = m 
            distance_lev = abs(m-n)
            # cost of substitution could be improved:
            # currently delete the last blocks of the longer sequence
            for i in range(shorter):
                if s1[i] != s2[i]:
                    distance_lev += 1
            distance = distance_lev/n
            return distance

        distance_substitution = 0
        for i in range(m):
            #print("at position", i, "  s1:", s1[i], "  s2:", s2[i])
            if s1[i] != s2[i]:
                distance_substitution += 1
        """
            Usually there's also deletion and insertion operations in levenshtein distance,
            yet in our case, these two distances should always be 0, 
            since the number of blocks are assured to be the same.
        """

        # normalize the distance into [0,1] range
        distance = distance_substitution/n

        return distance