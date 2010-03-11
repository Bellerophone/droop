#!/usr/bin/env python
"Count election using Reference WIGM STV"

import sys, os
path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if path not in sys.path: sys.path.insert(0, os.path.normpath(path))
from modules.election import Election

class Rule:
    '''
    Rule for counting Model WIGM elections
    
    Parameter: arithmetic type
    '''
    
    @staticmethod
    def init(arithmetic=None, precision=6, guard=None):
        "initialize election parameters"
        
        #  set defaults
        #
        if arithmetic is None: arithmetic = 'fixed'
        if arithmetic == 'rational':
            precision = guard = None
        elif arithmetic == 'qx':
            if precision is None:
                precision = 9
                guard = None
        elif arithmetic == 'fixed':
            if precision is None: precision = 6
            guard = 0
        elif arithmetic == 'integer':
            precision = guard = 0
        else:
            raise TypeError('unrecognized arithmetic type (%s)' % arithmetic)

        #  create an election
        #
        e = Election(Rule, precision, guard)
        return e

    @staticmethod
    def info(e):
        "return an info string for the election report"
        return "Model Weighted Inclusive Gregory Method (WIGM)"

    #########################
    #
    #   Main Election Counter
    #
    #########################
    @staticmethod
    def count(e):
        "count the election"
        
        #  local support functions
        #
        def hasQuota(e, candidate):
            '''
            Determine whether a candidate has a quota.
            
            If using exact arithmetic, then: vote > quota
            Otherwise: vote >= quota, since quota has been rounded up
            '''
            if e.V.exact:
                return candidate.vote > e.R.quota
            return candidate.vote >= e.R.quota
    
        def calcQuota(e):
            '''
            Calculate quota.
            
            Round up if not using exact arithmetic.
            '''
            if e.V.exact:
                return e.V(e.profile.nballots) / e.V(e.profile.nseats+1)
            return e.V(e.profile.nballots) / e.V(e.profile.nseats+1) + e.V.epsilon
        
        def breakTie(e, tied, purpose=None, strong=True):
            '''
            break a tie
            
            purpose must be 'surplus' or 'elect' or 'defeat', 
            indicating whether the tie is being broken for the purpose 
            of choosing a surplus to transfer, a winner, 
            or a candidate to eliminate. 
            
            Set strong to False to indicate that weak tiebreaking should be
            attempted, if relevant. Otherwise the tie is treated as strong.
            
            Not all tiebreaking methods will care about 'purpose' or 'strength',
            but the requirement is enforced for consistency of interface.
            '''
            assert purpose in ('surplus', 'elect', 'defeat')
            if not tied:
                return None
            if len(tied) == 1:
                return tied[0]
            if len(tied) > 1:
                t = tied[0]  # TODO: real tiebreaker
                s = 'Break tie (%s): [' % purpose
                s += ", ".join([c.name for c in tied])
                s += '] -> %s' % t.name
                e.R.log(s)
                return t

        #  Calculate quota
        #
        e.R0.quota = calcQuota(e)
        R = e.R0  # current round
        C = R.C   # candidate state
        V = e.V   # arithmetic value class
        
        #  Count votes in round 0 for reporting purposes
        #
        for c in C.hopeful:
            c.vote = V(0)
        for b in [b for b in R.ballots if not b.exhausted]:
            b.top.vote = b.top.vote + b.vote

        while C.nHopefulOrElected > e.profile.nseats and \
               C.nElected < e.profile.nseats:
            R = e.newRound()
            C = R.C   # candidate state

            #  count votes for hopeful or pending-transfer candidates
            #
            for c in C.hopefulOrPending:
                c.vote = V(0)
            for b in [b for b in R.ballots if not b.exhausted]:
                b.top.vote = b.top.vote + b.vote

            #  elect new winners
            #
            for c in [c for c in C.hopeful if hasQuota(e, c)]:
                C.elect(c, pending=True)  # elect with transfer pending
                if c.vote == R.quota:     # handle new winners with no surplus
                    R.advance(c)
                    C.unpend(c)
        
            #  find highest surplus
            #
            high_vote = R.quota
            high_candidates = []
            for c in C.elected:
                if c.vote == high_vote:
                    high_candidates.append(c)
                elif c.vote > high_vote:
                    high_vote = c.vote
                    high_candidates = [c]
            
            # transfer highest surplus
            #
            if high_vote > R.quota:
                # transfer surplus
                high_candidate = breakTie(e, high_candidates, 'surplus')
                surplus = high_vote - R.quota
                for b in [b for b in R.ballots if b.top == high_candidate]:
                    b.weight = (b.weight * surplus) / high_vote
                R.advance(high_candidate)
                C.unpend(high_candidate)
                high_candidate.vote = R.quota

            #  if no surplus to transfer, eliminate a candidate
            #
            else:
                #  find candidate(s) with lowest vote
                #
                low_vote = R.quota
                low_candidates = []
                for c in C.hopeful:
                    if c.vote == low_vote:
                        low_candidates.append(c)
                    elif c.vote < low_vote:
                        low_vote = c.vote
                        low_candidates = [c]

                #  defeat candidate with lowest vote
                #
                if low_candidates:
                    low_candidate = breakTie(e, low_candidates, 'defeat')
                    C.defeat(low_candidate)
                    R.advance(low_candidate)
        
        #  Election over.
        #  Elect or defeat remaining hopeful candidates
        #
        for c in C.pending:
            C.unpend(c)
        for c in C.hopeful.copy():
            if C.nElected < e.profile.nseats:
                C.elect(c, msg='Elect remaining', pending=False)
            else:
                C.defeat(c, msg='Defeat remaining')
    
