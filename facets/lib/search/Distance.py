import numpy as np
import math
from fractions import Fraction
#from javalang.javadoc import blocks_justify_re


class Distance:
    alphabet = None
    weight_deletion = 1
    weight_insertion = 1
    weight_substitution = 1
    weight_fragmentation = 1
    weight_consolidation = 1
    weight_swap = 1.5

    def __init__(self, alphabet=None):
        self.alphabet = alphabet

    @staticmethod
    def distance_hamming(s1, s2):
        # if len(s1) != len(s2):
        #    raise ValueError("Lists must be the same size")
        d = 0
        for i in range(min(len(s1), len(s2))):
            if s1[i] != s2[i]:
                d += 1
        return d

    @staticmethod
    def distance_hamming_difference(s1, s2):
        #
        #   Extended Hamming distance
        #   For lists of the same size, and containing only numbers
        #
        if len(s1) != len(s2):
            raise ValueError("Lists must be the same size")
        d = 0
        for i in range(len(s1)):
            d += abs(s1[i] - s2[i])
        return d

    @staticmethod
    def distance_euclidean(s1, s2):
        #
        #   Euclidean Hamming distance
        #   For lists of the same size, and containing only numbers
        #
        if len(s1) != len(s2):
            raise ValueError("Lists must have the same length")
        d = 0
        for i in range(len(s1)):
            d += pow(s1[i] - s2[i], 2)
        return math.sqrt(d)

    @staticmethod
    def edit_distance_restricted(s1, s2, operations):
        #
        # Calculate restricted edit distance
        # operations is a list of tuples : (left, right, cost) where o: left -> right is an operation
        #
        m = len(s1)
        n = len(s2)
        d = np.zeros([m + 1, n + 1])
        for i in range(0, m + 1):
            for j in range(0, n + 1):
                if i == 0 and j == 0:
                    continue
                if s1[i - 1] == s2[j - 1] and i != 0 and j != 0:
                    d[i, j] = d[i-1, j-1]
                else:
                    d_o = list()
                    for o in operations:
                        k = len(o.left)
                        r = len(o.right)
                        if k > i + 1 or r > j + 1:
                            continue
                        # Get possible operations
                        if s1[i-k:i] == o.left and s2[j-r:j] == o.right:
                            d_o.append(d[i-k, j-r] + o.cost)
                    if not d_o:
                        raise ValueError("Aucune opération possible.")
                    d[i, j] = min(d_o)
        return d[m, n]

    @staticmethod
    def edit_distance_extended(s1, s2):
        m = len(s1)
        n = len(s2)
        N = 1 # Nombre de caractères que l'on peut modifier dans la partie inactive

    def distance_levenshtein(self, s1, s2):
        #
        #   Compute Levenshtein distance between two sequences
        #
        m = len(s1)
        n = len(s2)
        d = np.zeros([m + 1, n + 1])
        for i in range(0, m + 1):
            d[i, 0] = i
        for j in range(0, n + 1):
            d[0, j] = j

        for j in range(1, n + 1):
            for i in range(1, m + 1):
                if s1[i - 1] == s2[j - 1]:
                    d[i, j] = d[i-1, j-1]
                else:
                    d[i, j] = min(
                                d[i-1, j] + self.weight_deletion,
                                d[i, j-1] + self.weight_insertion,
                                d[i-1, j-1] + self.weight_substitution
                            )
        return d[m, n]

    def distance_damerau_levenshtein_restricted(self, s1, s2):
        #
        # Compute edit distance with four operations :
        # Insertion, deletion, substitution and transposition of two adjacent symbols
        #
        operations = self.get_levenshtein_operations(self.alphabet) + self.get_swap_operations(self.alphabet)
        return self.edit_distance_restricted(s1, s2, operations)

    def distance_ms(self, s1, s2):
        #
        # Compute edit distance as defined by Mongeau & Sankoff
        #
        m = len(s1)
        n = len(s2)
        d = np.zeros([m + 1, n + 1])
        for i in range(0, m + 1):
            d[i, 0] = i
        for j in range(0, n + 1):
            d[0, j] = j

        path = list()
        for j in range(1, n + 1):
            for i in range(1, m + 1):
                if s1[i - 1] == s2[j - 1]:
                    d[i, j] = d[i-1, j-1]
                    path.append((0, "MATCH"))
                else:
                    operations = list()
                    operations.append((d[i-1, j] + self.weight_deletion, "DELETION"))
                    operations.append((d[i, j-1] + self.weight_insertion, "INSERTION"))
                    operations.append((d[i-1, j-1] + self.weight_substitution, "SUBSTITUTION"))
                    # Fragmentation
                    for k in range(2, j):
                        # Check if notes are similar
                        if len(set(s2[j-k:j])) > 1:
                            continue
                        operations.append((d[i-1, j-k] + self.weight_fragmentation, "FRAGMENTATION " + str(k)))
                    # Consolidation
                    for l in range(2, i):
                        # Check if notes are similar
                        if len(set(s1[i-l:i])) > 1:
                            continue
                        operations.append((d[i-l, j-1] + self.weight_consolidation, "CONSOLIDATION " + str(l)))
                    index, minimum = self.minimum(operations)
                    path.append(operations[index])
                    d[i, j] = minimum[0]
        return d[m, n]

    @staticmethod
    def rythmic_distance(r1, r2):
        """
          Compute Levenshtein distance between two sequences
        """
        
        # Bad hack from Philippe: math.inf exists in 3.5 
        MATH_INF = -1000000000
        m = len(r1)
        n = len(r2)
        d = np.zeros([m, n])
        gap_cost = 1
        for i in range(0, m):
           # d[i, 0] = math.inf
           print ("Rythm 1 : " + str(r1[i]["start_pos"]), str(r1[i]["end_pos"]),
                  str(r1[i]["pitch_change"]), str(r1[i]["gap"]))
           d[i, 0] = MATH_INF
        for j in range(0, n):
           # d[0, j] = math.inf
           d[0, j] = MATH_INF
           print ("Rythm 2  : " + str(r2[i]["start_pos"]), str(r2[i]["end_pos"]),
                  str(r2[i]["pitch_change"]), str(r2[i]["gap"]))
        d[0, 0] = 0
        
        return 1


    @staticmethod
    def dtw(s1, s2):
        #
        #   Compute Levenshtein distance between two sequences
        #
        # Bad hack from Philippe: math.inf exists in 3.5 
        MATH_INF = -1000000000
        m = len(s1)
        n = len(s2)
        d = np.zeros([m, n])
        gap_cost = 1
        for i in range(0, m):
           # d[i, 0] = math.inf
            d[i, 0] = MATH_INF
        for j in range(0, n):
           # d[0, j] = math.inf
           d[0, j] = MATH_INF
        d[0, 0] = 0
        for j in range(1, n):
            for i in range(1, m):
                # Cost depends on rhythm and pitch differences
                cost = abs(float(Fraction(s1[i-1]['rhythm'])) - float(Fraction(s2[j-1]['rhythm'])))
                d[i, j] = min(d[i - 1, j] + cost + gap_cost,
                              d[i, j - 1] + cost + gap_cost,
                              d[i - 1, j - 1] + cost)
        # Take best local alignment between full strings
        # e.g. distance("abc", "abcd") = 0
        distance = min(min(d[:, n-1]), min(d[m-1, :]))
        return distance

    def test_distance(self):
        a = [{'end_pos': '1', 'start_pos': '0', 'rhythm': '1', 'pitch': '0'}, {'end_pos': '2', 'start_pos': '1', 'rhythm': '1/2', 'pitch': '0'}, {'end_pos': '3', 'start_pos': '2', 'rhythm': '1', 'pitch': '-5'}, {'end_pos': '4', 'start_pos': '3', 'rhythm': '1', 'pitch': '3'}]
        b = [{'end_pos': '1', 'start_pos': '0', 'rhythm': '2', 'pitch': '-5'}, {'end_pos': '2', 'start_pos': '1', 'rhythm': '1/2', 'pitch': '3'}, {'end_pos': '3', 'start_pos': '2', 'rhythm': '1', 'pitch': '2'}]

        print(self.distance_dtw(a, b))

    def get_levenshtein_operations(self, alphabet):
        #
        #   Return list of all possible Levenshtein operations
        #
        operations = list()
        l = len(alphabet)
        for i in range(0, l):
            operations.append(Operation(left=alphabet[i], right="", cost=self.weight_deletion)) # Deletion
            operations.append(Operation(left="", right=alphabet[i], cost=self.weight_insertion)) # Insertions
            for j in range(0, l):
                if alphabet[i] != alphabet[j]:
                    operations.append(Operation(left=alphabet[i], right=alphabet[j], cost=self.weight_substitution)) # Substitution
        return operations

    def get_insertion_operations(self, alphabet):
        operations = list()
        for l in alphabet:
            operations.append(Operation(left="", right=l, cost=self.weight_insertion))
        return operations

    def get_deletion_operations(self, alphabet):
        operations = list()
        for l in alphabet:
            operations.append(Operation(left=l, right="", cost=self.weight_deletion))
        return operations

    def get_substitution_operations(self, alphabet):
        operations = list()
        l = len(alphabet)
        for i in range(0, l):
            for j in range(0, l):
                if i != j:
                    operations.append(Operation(left=alphabet[i], right=alphabet[j], cost=self.weight_substitution))
        return operations

    def get_swap_operations(self, alphabet):
        operations = list()
        l = len(alphabet)
        for i in range(0, l):
            for j in range(0, l):
                if i != j:
                    operations.append(Operation(left=alphabet[i] + alphabet[j], right=alphabet[j] + alphabet[i], cost=self.weight_swap))
        return operations

    def operation_set_closure(self, operations):
        closed_set = set(operations)
        queue = operations
        while queue:
            o = queue.pop(0)
            possible_operations = self.get_possible_operations(o.right, operations)
            for p_o in possible_operations:
                new_operation = Operation(left=o.right, right=self.get_operation_result(o.right, p_o), cost=o.cost + p_o.cost)
                closed_set.add(new_operation)
                queue.append(new_operation)
        return list(closed_set)

    @staticmethod
    def get_possible_operations(s, operations):
        possible_operations = list()
        for o in operations:
            if o.left in s:
                possible_operations.append(o)
        return possible_operations

    @staticmethod
    def get_possible_operations_extended(s1, s2, k, operations):
        m = len(s1)
        n = len(s2)
        if k > m:
            raise ValueError("k hors limite.")
        for o in operations:
            p = len(o.left)
            q = len(o.right)

    @staticmethod
    def get_operation_result(s, operation):
        if operation.left not in s:
            raise ValueError("Opération impossible.")
        return s.replace(operation.left, operation.right, 1)

    @staticmethod
    def minimum(l):
        #
        # Get minimum and its index in the list
        #
        minimum = l[0]
        i_min = 0
        for i, item in enumerate(l):
            if item < minimum:
                minimum = item
                i_min = i
        return i_min, minimum


    @staticmethod
    def distance_pr(s1, s2):
        """Special distance measure for Neuma. The input consists of two sequences
        that share the same melodic profile: we know that the sucession of intervals is the same.
        The functions cuts each sequence in blocks of constant-pitch notes. Two successive
        blocks correspond to distinct pitches, and, as explained, the intervals between
        blocks in both sequences are pairwise equal.
        Therefore we measure the rythmic distance for each pair of block, and cumulate them."""
        
        # Sanity check
        if len(s1.items) == 0 or len(s2.items) == 0:
            return 1000000 # Find sth cleaner
        
        # Compute blocks ranges
        blocks1 = Distance.find_blocks_range(s1)
        blocks2 = Distance.find_blocks_range(s2)

        # Check: the number of block should be the same
        if len(blocks1) != len(blocks2):
            raise ValueError("Distance computation between the pattern andf an occurrence: the number of intervals is inconsistent")
        
        blocks1  = Distance.normalize_block_duration(blocks1)
        blocks2  = Distance.normalize_block_duration(blocks2)
        
        cost_alignment = 0
        for iblock in range(len(blocks1)):
            block1 = blocks1[iblock]
            block2 = blocks2[iblock]
            
            #print ("Block " + str(iblock) + ". Seq1: [" + str(block1["start_pos"]) + "," + str(block1["end_pos"]) + 
            #    "] duration " + str(block1["duration"])
            #                         + " Seq2 [" + str(block2["start_pos"]) + "," + str(block2["end_pos"]) + 
            #    "] duration " + str(block2["duration"]))
            
            # The sum of the normalized durations gaps represents the cost of aligning the 
            # two sequences of durations
            cost_alignment += abs(block1["duration"] - block2["duration"])
            
            #
            # We can even dop better by taking account of the internal rhythm of each block. 
            # An approximation is simply to compare the number of events in each block
            
            #
            # What is the rhythmic ratio between the duration of two successive blocks (Not useful??)
            if iblock < len(blocks1) - 1:
                ratio1 = block1["duration"] /  blocks1[iblock+1]["duration"]
                ratio2 = block2["duration"] /  blocks2[iblock+1]["duration"]
                # print ("Ratio 1 " + str(ratio1) + " ratio 2 " + str(ratio2))
                
        return cost_alignment

    @staticmethod
    def find_blocks_range(s):
        """Take a sequence and compute the ranges of 'blocks', where a block
        is a sequence if similar pitches"""
        start_current_block = 0
        block_ranges = []
        current_pos = 0
        block_duration = 0
        for item in s.items:
            if item.get_index() != s.items[start_current_block].get_index():
                block_ranges.append({"start_pos": start_current_block, "end_pos": current_pos-1, "duration": block_duration})
                start_current_block = current_pos
                block_duration = 0
            current_pos = current_pos+1
            block_duration += item.duration
        block_ranges.append({"start_pos": start_current_block, "end_pos": len(s.items), "duration": block_duration})
        return block_ranges

    @staticmethod
    def normalize_block_duration(blocks):
        """Normalize the duration of a sequence of blocks"""
        full_duration = 0
        for block in blocks:
            full_duration += block["duration"]
        for block in blocks:
             block["duration"] = block["duration"] / full_duration
        
        return blocks

class Operation:
    left = None
    right = None
    cost = 0

    def __init__(self, left, right, cost):
        self.left = left
        self.right = right
        self.cost = cost
