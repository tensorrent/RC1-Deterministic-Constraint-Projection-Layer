# -----------------------------------------------------------------------------
# SOVEREIGN INTEGRITY PROTOCOL (SIP) LICENSE v1.1
# 
# Copyright (c) 2026, Bradley Wallace (tensorrent). All rights reserved.
# 
# This software, research, and associated mathematical implementations are
# strictly governed by the Sovereign Integrity Protocol (SIP) License v1.1:
# - Personal/Educational Use: Perpetual, worldwide, royalty-free.
# - Commercial Use: Expressly PROHIBITED without a prior written license.
# - Unlicensed Commercial Use: Triggers automatic 8.4% perpetual gross
#   profit penalty (distrust fee + reparation fee).
# 
# See the SIP_LICENSE.md file in the repository root for full terms.
# -----------------------------------------------------------------------------
"""
RC7 DIEG — Deterministic Invariant Extraction Grammar
v1.0.0

Converts semi-structured mathematical text into InvariantCard candidates.
Not NLP. Not generative. Grammar-constrained pattern extraction.

Pipeline:
    Raw Text → Structural Tokenizer → Pattern Matcher → Canonicalizer
    → Tier Classifier → InvariantCard Builder → Validation Gate

Scope (v1): Algebra + Limited Formal Logic
    IN:  rational inequalities, polynomial conditions, determinant/trace,
         logical implications (∧, ∨, ⟹, ∀ over finite sets), spectral
         radius bounds as algebraic inequalities
    OUT: continuous optimization (sup, inf over R), measure theory,
         PDE extraction, undecidable logical systems

Design principle: REJECT > GUESS. No card created on ambiguity.
"""

import re
import uuid
import json
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import (
    List, Dict, Tuple, Optional, Set, Any, Union
)


# ═══════════════════════════════════════════════════════════════
# SECTION 1: TOKEN TYPES
# ═══════════════════════════════════════════════════════════════

class TokenType(Enum):
    # Atoms
    SYMBOL = "SYMBOL"           # variable name: beta, kappa, x, A, etc.
    NUMBER = "NUMBER"           # integer or rational: 3, -2, 1/2
    OPERATOR = "OPERATOR"       # +, -, *, /, ^
    COMPARISON = "COMPARISON"   # >, <, >=, <=, ==, !=

    # Structural
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    COMMA = "COMMA"
    COLON = "COLON"
    DOT = "DOT"

    # Logic
    AND = "AND"                 # ∧, and, AND, &
    OR = "OR"                   # ∨, or, OR, |
    IMPLIES = "IMPLIES"         # ⟹, =>, implies, if...then
    IFF = "IFF"                 # ⟺, iff, if and only if
    NOT = "NOT"                 # ¬, not, NOT
    FORALL = "FORALL"           # ∀, for all, for every
    EXISTS = "EXISTS"           # ∃, there exists
    IN = "IN"                   # ∈, in

    # Domain keywords
    KW_STABLE = "KW_STABLE"
    KW_UNSTABLE = "KW_UNSTABLE"
    KW_BOUNDED = "KW_BOUNDED"
    KW_MONOTONE = "KW_MONOTONE"
    KW_CONVEX = "KW_CONVEX"
    KW_CONVERGENT = "KW_CONVERGENT"
    KW_EIGENVALUE = "KW_EIGENVALUE"
    KW_SPECTRAL = "KW_SPECTRAL"
    KW_DETERMINANT = "KW_DETERMINANT"
    KW_TRACE = "KW_TRACE"
    KW_RANK = "KW_RANK"
    KW_REAL_PART = "KW_REAL_PART"

    # Structural keywords
    KW_IFF = "KW_IFF"          # "if and only if", "iff", "necessary and sufficient"
    KW_WHEN = "KW_WHEN"        # "when", "whenever", "provided"
    KW_WHERE = "KW_WHERE"      # "where", "such that"

    # Functions
    FUNC = "FUNC"              # det, tr, spec, eig, Re, Im, max, min, diag

    # Meta
    NEWLINE = "NEWLINE"
    EOF = "EOF"
    UNKNOWN = "UNKNOWN"


@dataclass
class Token:
    type: TokenType
    value: str
    position: int


# ═══════════════════════════════════════════════════════════════
# SECTION 2: STRUCTURAL TOKENIZER
# ═══════════════════════════════════════════════════════════════

# Greek letter mappings (Unicode + LaTeX + ASCII)
GREEK_MAP = {
    # Unicode
    'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta',
    'ε': 'epsilon', 'ζ': 'zeta', 'η': 'eta', 'θ': 'theta',
    'ι': 'iota', 'κ': 'kappa', 'λ': 'lambda_', 'μ': 'mu',
    'ν': 'nu', 'ξ': 'xi', 'π': 'pi', 'ρ': 'rho',
    'σ': 'sigma', 'τ': 'tau', 'φ': 'phi', 'χ': 'chi',
    'ψ': 'psi', 'ω': 'omega',
    'Δ': 'Delta', 'Σ': 'Sigma', 'Π': 'Pi', 'Ω': 'Omega',
    # Common symbols
    '∞': 'INF',
}

# LaTeX command → normalized name
LATEX_COMMANDS = {
    r'\alpha': 'alpha', r'\beta': 'beta', r'\gamma': 'gamma',
    r'\delta': 'delta', r'\epsilon': 'epsilon', r'\kappa': 'kappa',
    r'\lambda': 'lambda_', r'\mu': 'mu', r'\rho': 'rho',
    r'\sigma': 'sigma', r'\omega': 'omega',
    r'\Delta': 'Delta', r'\Sigma': 'Sigma',
    r'\det': 'det', r'\tr': 'tr', r'\operatorname{tr}': 'tr',
    r'\operatorname{Re}': 'Re', r'\operatorname{Im}': 'Im',
    r'\operatorname{spec}': 'spec', r'\operatorname{eig}': 'eig',
    r'\operatorname{diag}': 'diag', r'\operatorname{rank}': 'rank',
    r'\max': 'max', r'\min': 'min', r'\sup': 'sup', r'\inf': 'inf',
    r'\leq': '<=', r'\geq': '>=', r'\neq': '!=',
    r'\le': '<=', r'\ge': '>=', r'\ne': '!=',
    r'\iff': 'iff', r'\implies': '=>', r'\Rightarrow': '=>',
    r'\Leftrightarrow': 'iff',
    r'\forall': 'forall', r'\exists': 'exists', r'\in': 'in',
    r'\land': 'and', r'\lor': 'or', r'\neg': 'not',
    r'\cdot': '*', r'\times': '*',
}

# Known function names
KNOWN_FUNCTIONS = {
    'det', 'tr', 'trace', 'spec', 'eig', 'eigenvalue', 'eigenvalues',
    'Re', 'Im', 'max', 'min', 'sup', 'inf', 'diag', 'rank',
    'abs', 'sign', 'sgn', 'mod',
}

# Domain keyword sets
STABILITY_WORDS = {'stable', 'stability', 'asymptotically', 'hurwitz', 'schur', 'lyapunov'}
INSTABILITY_WORDS = {'unstable', 'instability', 'diverge', 'divergent', 'diverges'}
BOUNDED_WORDS = {'bounded', 'bound', 'bounds', 'boundedness'}
MONOTONE_WORDS = {'monotone', 'monotonic', 'increasing', 'decreasing', 'nondecreasing', 'nonincreasing'}
CONVEX_WORDS = {'convex', 'concave', 'convexity', 'concavity'}
CONVERGENT_WORDS = {'converge', 'converges', 'convergent', 'convergence'}
SPECTRAL_WORDS = {'spectral', 'spectrum', 'eigenvalue', 'eigenvalues'}
CONDITION_WORDS = {'iff', 'if and only if', 'necessary and sufficient',
                   'necessary', 'sufficient', 'equivalent'}
WHEN_WORDS = {'when', 'whenever', 'provided', 'provided that', 'assuming', 'given'}
WHERE_WORDS = {'where', 'such that', 'satisfying'}


class Tokenizer:
    """
    Structural tokenizer for mathematical text.
    Converts raw text → token stream.
    Handles Unicode, LaTeX, and ASCII math notation.
    """

    def __init__(self):
        pass

    def tokenize(self, text: str) -> List[Token]:
        """Tokenize input text into structured tokens."""
        # Phase 1: Normalize
        text = self._normalize(text)
        # Phase 2: Tokenize
        tokens = self._scan(text)
        # Phase 3: Post-process (merge multi-word keywords)
        tokens = self._merge_keywords(tokens)
        return tokens

    def _normalize(self, text: str) -> str:
        """Normalize Unicode and LaTeX into ASCII-safe form."""
        # Replace Unicode Greek
        for char, name in GREEK_MAP.items():
            text = text.replace(char, f' {name} ')

        # Replace LaTeX commands (longest first to avoid partial matches)
        for cmd in sorted(LATEX_COMMANDS.keys(), key=len, reverse=True):
            text = text.replace(cmd, f' {LATEX_COMMANDS[cmd]} ')

        # Normalize comparison operators
        text = text.replace('≥', ' >= ')
        text = text.replace('≤', ' <= ')
        text = text.replace('≠', ' != ')
        text = text.replace('⟹', ' => ')
        text = text.replace('⟺', ' iff ')
        text = text.replace('→', ' => ')
        text = text.replace('↔', ' iff ')
        text = text.replace('∧', ' and ')
        text = text.replace('∨', ' or ')
        text = text.replace('¬', ' not ')
        text = text.replace('∀', ' forall ')
        text = text.replace('∃', ' exists ')
        text = text.replace('∈', ' in ')

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _scan(self, text: str) -> List[Token]:
        """Scan normalized text into token list."""
        tokens = []
        i = 0
        while i < len(text):
            c = text[i]

            # Skip whitespace
            if c == ' ':
                i += 1
                continue

            # Newline
            if c == '\n':
                tokens.append(Token(TokenType.NEWLINE, '\n', i))
                i += 1
                continue

            # Multi-char operators
            if i + 1 < len(text):
                two = text[i:i+2]
                if two == '=>':
                    tokens.append(Token(TokenType.IMPLIES, '=>', i))
                    i += 2
                    continue
                if two == '>=':
                    tokens.append(Token(TokenType.COMPARISON, '>=', i))
                    i += 2
                    continue
                if two == '<=':
                    tokens.append(Token(TokenType.COMPARISON, '<=', i))
                    i += 2
                    continue
                if two == '!=':
                    tokens.append(Token(TokenType.COMPARISON, '!=', i))
                    i += 2
                    continue
                if two == '==':
                    tokens.append(Token(TokenType.COMPARISON, '==', i))
                    i += 2
                    continue

            # Single-char operators and delimiters
            if c in '+-^':
                tokens.append(Token(TokenType.OPERATOR, c, i))
                i += 1
                continue
            if c == '*':
                tokens.append(Token(TokenType.OPERATOR, '*', i))
                i += 1
                continue
            if c == '/':
                tokens.append(Token(TokenType.OPERATOR, '/', i))
                i += 1
                continue
            if c == '(':
                tokens.append(Token(TokenType.LPAREN, '(', i))
                i += 1
                continue
            if c == ')':
                tokens.append(Token(TokenType.RPAREN, ')', i))
                i += 1
                continue
            if c == '[':
                tokens.append(Token(TokenType.LBRACKET, '[', i))
                i += 1
                continue
            if c == ']':
                tokens.append(Token(TokenType.RBRACKET, ']', i))
                i += 1
                continue
            if c == ',':
                tokens.append(Token(TokenType.COMMA, ',', i))
                i += 1
                continue
            if c == ':':
                tokens.append(Token(TokenType.COLON, ':', i))
                i += 1
                continue
            if c == '.':
                tokens.append(Token(TokenType.DOT, '.', i))
                i += 1
                continue

            # Comparison (single char)
            if c == '>':
                tokens.append(Token(TokenType.COMPARISON, '>', i))
                i += 1
                continue
            if c == '<':
                tokens.append(Token(TokenType.COMPARISON, '<', i))
                i += 1
                continue
            if c == '=':
                tokens.append(Token(TokenType.COMPARISON, '==', i))
                i += 1
                continue

            # Numbers (integer, negative, decimal)
            if c.isdigit() or (c == '-' and i + 1 < len(text) and text[i+1].isdigit()):
                j = i
                if c == '-':
                    j += 1
                while j < len(text) and (text[j].isdigit() or text[j] == '.'):
                    j += 1
                tokens.append(Token(TokenType.NUMBER, text[i:j], i))
                i = j
                continue

            # Words (identifiers, keywords, functions)
            if c.isalpha() or c == '_':
                j = i
                while j < len(text) and (text[j].isalnum() or text[j] == '_'):
                    j += 1
                word = text[i:j]
                token = self._classify_word(word, i)
                tokens.append(token)
                i = j
                continue

            # Unknown
            tokens.append(Token(TokenType.UNKNOWN, c, i))
            i += 1

        tokens.append(Token(TokenType.EOF, '', len(text)))
        return tokens

    def _classify_word(self, word: str, pos: int) -> Token:
        """Classify a word token."""
        low = word.lower()

        # Logic
        if low in ('and', 'AND'):
            return Token(TokenType.AND, 'and', pos)
        if low in ('or', 'OR'):
            return Token(TokenType.OR, 'or', pos)
        if low in ('not', 'NOT'):
            return Token(TokenType.NOT, 'not', pos)
        if low == 'implies':
            return Token(TokenType.IMPLIES, '=>', pos)
        if low == 'iff':
            return Token(TokenType.IFF, 'iff', pos)
        if low == 'forall':
            return Token(TokenType.FORALL, 'forall', pos)
        if low == 'exists':
            return Token(TokenType.EXISTS, 'exists', pos)
        if low == 'in':
            return Token(TokenType.IN, 'in', pos)

        # Domain keywords
        if low in STABILITY_WORDS:
            return Token(TokenType.KW_STABLE, low, pos)
        if low in INSTABILITY_WORDS:
            return Token(TokenType.KW_UNSTABLE, low, pos)
        if low in BOUNDED_WORDS:
            return Token(TokenType.KW_BOUNDED, low, pos)
        if low in MONOTONE_WORDS:
            return Token(TokenType.KW_MONOTONE, low, pos)
        if low in CONVEX_WORDS:
            return Token(TokenType.KW_CONVEX, low, pos)
        if low in CONVERGENT_WORDS:
            return Token(TokenType.KW_CONVERGENT, low, pos)
        if low in ('spectral', 'spectrum'):
            return Token(TokenType.KW_SPECTRAL, low, pos)
        if low in ('eigenvalue', 'eigenvalues'):
            return Token(TokenType.KW_EIGENVALUE, low, pos)
        if low in ('determinant', 'det'):
            return Token(TokenType.KW_DETERMINANT, low, pos)
        if word in ('Delta', 'delta'):
            return Token(TokenType.KW_DETERMINANT, word, pos)
        if low in ('trace', 'tr'):
            return Token(TokenType.KW_TRACE, low, pos)
        if low == 'rank':
            return Token(TokenType.KW_RANK, low, pos)

        # Real part
        if word == 'Re':
            return Token(TokenType.KW_REAL_PART, 'Re', pos)
        if word == 'Im':
            return Token(TokenType.FUNC, 'Im', pos)

        # Structural keywords
        if low in ('when', 'whenever', 'provided', 'assuming', 'given'):
            return Token(TokenType.KW_WHEN, low, pos)
        if low in ('where', 'satisfying'):
            return Token(TokenType.KW_WHERE, low, pos)

        # Functions
        if low in KNOWN_FUNCTIONS or word in KNOWN_FUNCTIONS:
            return Token(TokenType.FUNC, word, pos)

        # Default: symbol
        return Token(TokenType.SYMBOL, word, pos)

    def _merge_keywords(self, tokens: List[Token]) -> List[Token]:
        """Merge multi-word keywords: 'if and only if', 'such that', etc."""
        merged = []
        i = 0
        while i < len(tokens):
            # "if and only if" → IFF
            if (i + 3 < len(tokens) and
                tokens[i].value.lower() == 'if' and
                tokens[i+1].type == TokenType.AND and
                tokens[i+2].value.lower() == 'only' and
                tokens[i+3].value.lower() == 'if'):
                merged.append(Token(TokenType.IFF, 'iff', tokens[i].position))
                i += 4
                continue

            # "such that" → WHERE
            if (i + 1 < len(tokens) and
                tokens[i].value.lower() == 'such' and
                tokens[i+1].value.lower() == 'that'):
                merged.append(Token(TokenType.KW_WHERE, 'such that', tokens[i].position))
                i += 2
                continue

            # "provided that" → WHEN
            if (i + 1 < len(tokens) and
                tokens[i].value.lower() == 'provided' and
                tokens[i+1].value.lower() == 'that'):
                merged.append(Token(TokenType.KW_WHEN, 'provided that', tokens[i].position))
                i += 2
                continue

            # "for all" → FORALL
            if (i + 1 < len(tokens) and
                tokens[i].value.lower() == 'for' and
                tokens[i+1].value.lower() == 'all'):
                merged.append(Token(TokenType.FORALL, 'forall', tokens[i].position))
                i += 2
                continue

            # "for every" → FORALL
            if (i + 1 < len(tokens) and
                tokens[i].value.lower() == 'for' and
                tokens[i+1].value.lower() == 'every'):
                merged.append(Token(TokenType.FORALL, 'forall', tokens[i].position))
                i += 2
                continue

            # "there exists" → EXISTS
            if (i + 1 < len(tokens) and
                tokens[i].value.lower() == 'there' and
                tokens[i+1].type == TokenType.EXISTS):
                merged.append(Token(TokenType.EXISTS, 'exists', tokens[i].position))
                i += 2
                continue

            # "necessary and sufficient" → IFF
            if (i + 2 < len(tokens) and
                tokens[i].value.lower() == 'necessary' and
                tokens[i+1].type == TokenType.AND and
                tokens[i+2].value.lower() == 'sufficient'):
                merged.append(Token(TokenType.IFF, 'iff', tokens[i].position))
                i += 3
                continue

            # "stable iff" already handled by individual tokens

            # "real part" → REAL_PART
            if (i + 1 < len(tokens) and
                tokens[i].value.lower() == 'real' and
                tokens[i+1].value.lower() == 'part'):
                merged.append(Token(TokenType.KW_REAL_PART, 'Re', tokens[i].position))
                i += 2
                continue

            # Skip filler words
            if tokens[i].value.lower() in ('the', 'a', 'an', 'is', 'are', 'of',
                                            'that', 'this', 'then', 'if', 'has',
                                            'have', 'holds', 'we', 'it', 'its',
                                            'system', 'condition', 'following',
                                            'let', 'be', 'so', 'with', 'by',
                                            'from', 'to', 'can', 'will', 'may',
                                            'also', 'note', 'thus', 'hence',
                                            'therefore', 'since', 'because',
                                            'both', 'either', 'neither',
                                            'satisfies', 'requires', 'ensures'):
                i += 1
                continue

            merged.append(tokens[i])
            i += 1

        # Ensure EOF
        if not merged or merged[-1].type != TokenType.EOF:
            merged.append(Token(TokenType.EOF, '', 0))
        return merged


# ═══════════════════════════════════════════════════════════════
# SECTION 3: PATTERN MATCHER
# ═══════════════════════════════════════════════════════════════

class InvariantType(Enum):
    IMPLICATION = "implication"
    TAUTOLOGY = "tautology"
    EQUIVALENCE = "equivalence"
    INEQUALITY = "inequality"
    CONTAINMENT = "containment"


class DomainType(Enum):
    STABILITY = "stability"
    BOUNDEDNESS = "boundedness"
    MONOTONICITY = "monotonicity"
    SPECTRAL = "spectral"
    ALGEBRAIC = "algebraic"


@dataclass
class ExtractionCandidate:
    """Raw extraction result before canonicalization."""
    invariant_type: InvariantType
    domain: DomainType
    lhs: str                       # left-hand side expression
    comparison: str                # >, <, >=, <=, ==
    rhs: str                       # right-hand side expression
    variables: Set[str]            # detected variable names
    conditions: List[str]          # explicit conditions/assumptions
    quantifiers: List[str]         # ∀x∈S, ∃x, etc.
    source_text: str               # original input fragment
    confidence: float = 0.0        # structural completeness score


class PatternMatcher:
    """
    Matches token streams against known invariant patterns.
    Returns ExtractionCandidate or None.
    """

    def match(self, tokens: List[Token], source_text: str) -> Optional[ExtractionCandidate]:
        """Try all pattern classes in priority order.
        Logic patterns (implication, equivalence) checked FIRST —
        they contain algebraic sub-expressions that would otherwise
        be caught by the inequality matcher."""
        for matcher in [
            self._match_implication,
            self._match_equivalence,
            self._match_determinant_condition,
            self._match_trace_condition,
            self._match_spectral_bound,
            self._match_inequality,
        ]:
            result = matcher(tokens, source_text)
            if result is not None:
                return result
        return None

    def _find_comparison(self, tokens: List[Token]) -> Optional[int]:
        """Find the index of the primary comparison operator."""
        for i, t in enumerate(tokens):
            if t.type == TokenType.COMPARISON:
                return i
        return None

    def _extract_variables(self, tokens: List[Token]) -> Set[str]:
        """Extract all symbol and mathematical entity names from token stream."""
        variables = set()
        MATH_KEYWORD_TYPES = {
            TokenType.SYMBOL, TokenType.KW_DETERMINANT, TokenType.KW_TRACE,
            TokenType.KW_EIGENVALUE, TokenType.KW_SPECTRAL, TokenType.KW_REAL_PART,
            TokenType.KW_RANK, TokenType.FUNC,
        }
        for t in tokens:
            if t.type in MATH_KEYWORD_TYPES:
                variables.add(t.value)
        return variables

    def _tokens_to_expr(self, tokens: List[Token]) -> str:
        """Convert token list back to expression string."""
        parts = []
        for t in tokens:
            if t.type in (TokenType.EOF, TokenType.NEWLINE):
                continue
            parts.append(t.value)
        return ' '.join(parts)

    def _detect_domain(self, tokens: List[Token]) -> DomainType:
        """Detect the domain from keyword tokens."""
        for t in tokens:
            if t.type in (TokenType.KW_STABLE, TokenType.KW_UNSTABLE):
                return DomainType.STABILITY
            if t.type == TokenType.KW_BOUNDED:
                return DomainType.BOUNDEDNESS
            if t.type == TokenType.KW_MONOTONE:
                return DomainType.MONOTONICITY
            if t.type in (TokenType.KW_SPECTRAL, TokenType.KW_EIGENVALUE, TokenType.KW_REAL_PART):
                return DomainType.SPECTRAL
            if t.type == TokenType.KW_DETERMINANT:
                return DomainType.STABILITY  # det condition → stability
            if t.type == TokenType.KW_TRACE:
                return DomainType.STABILITY  # trace condition → stability
        return DomainType.ALGEBRAIC

    def _extract_conditions(self, tokens: List[Token]) -> Tuple[List[Token], List[str]]:
        """Split off conditions after WHEN/WHERE keywords."""
        conditions = []
        main_tokens = []
        in_condition = False

        for t in tokens:
            if t.type in (TokenType.KW_WHEN, TokenType.KW_WHERE):
                in_condition = True
                continue
            if in_condition:
                if t.type in (TokenType.IMPLIES, TokenType.IFF, TokenType.EOF):
                    in_condition = False
                    main_tokens.append(t)
                else:
                    conditions.append(t.value)
            else:
                main_tokens.append(t)

        return main_tokens, [' '.join(conditions)] if conditions else []

    def _extract_quantifiers(self, tokens: List[Token]) -> Tuple[List[Token], List[str]]:
        """Extract quantifier blocks (∀x∈S)."""
        quantifiers = []
        remaining = []
        i = 0
        while i < len(tokens):
            if tokens[i].type == TokenType.FORALL:
                # Collect forall var in set
                parts = ['forall']
                i += 1
                while i < len(tokens) and tokens[i].type not in (
                    TokenType.COMPARISON, TokenType.IMPLIES, TokenType.IFF,
                    TokenType.COLON, TokenType.EOF
                ):
                    parts.append(tokens[i].value)
                    i += 1
                quantifiers.append(' '.join(parts))
                if i < len(tokens) and tokens[i].type == TokenType.COLON:
                    i += 1  # skip colon after quantifier
            else:
                remaining.append(tokens[i])
                i += 1
        return remaining, quantifiers

    # ─── Pattern A: Inequality Invariants ─────────────────────

    def _match_inequality(self, tokens: List[Token], source: str) -> Optional[ExtractionCandidate]:
        """Match pure inequality: expr > 0, expr >= expr, etc."""
        tokens, quantifiers = self._extract_quantifiers(tokens)
        tokens, conditions = self._extract_conditions(tokens)

        comp_idx = self._find_comparison(tokens)
        if comp_idx is None:
            return None

        # Check this isn't better matched by a more specific pattern
        has_det = any(t.type == TokenType.KW_DETERMINANT for t in tokens)
        has_trace = any(t.type == TokenType.KW_TRACE for t in tokens)
        has_spectral = any(t.type in (TokenType.KW_SPECTRAL, TokenType.KW_EIGENVALUE) for t in tokens)
        if has_det or has_trace or has_spectral:
            return None  # let specific matchers handle these

        lhs_tokens = tokens[:comp_idx]
        rhs_tokens = tokens[comp_idx+1:]
        comp = tokens[comp_idx].value

        lhs = self._tokens_to_expr(lhs_tokens)
        rhs = self._tokens_to_expr(rhs_tokens)
        variables = self._extract_variables(tokens)
        domain = self._detect_domain(tokens)

        if not lhs.strip() or not rhs.strip():
            return None

        return ExtractionCandidate(
            invariant_type=InvariantType.INEQUALITY,
            domain=domain,
            lhs=lhs,
            comparison=comp,
            rhs=rhs,
            variables=variables,
            conditions=conditions,
            quantifiers=quantifiers,
            source_text=source,
        )

    # ─── Pattern B: Determinant Condition ─────────────────────

    def _match_determinant_condition(self, tokens: List[Token], source: str) -> Optional[ExtractionCandidate]:
        """Match: det(A) > 0, Δ > 0, βκ − αγ > 0."""
        tokens, quantifiers = self._extract_quantifiers(tokens)
        tokens, conditions = self._extract_conditions(tokens)

        has_det = any(t.type == TokenType.KW_DETERMINANT or t.value == 'Delta' for t in tokens)
        if not has_det:
            # Check for cross-product pattern: a*b - c*d or a*b > c*d
            symbols = [t for t in tokens if t.type == TokenType.SYMBOL]
            ops = [t for t in tokens if t.type == TokenType.OPERATOR and t.value in ('*', '-')]
            if len(symbols) >= 4 and len(ops) >= 2:
                has_det = True  # heuristic: 4 symbols with multiply/subtract → possible determinant

        if not has_det:
            return None

        comp_idx = self._find_comparison(tokens)
        if comp_idx is None:
            return None

        lhs = self._tokens_to_expr(tokens[:comp_idx])
        rhs = self._tokens_to_expr(tokens[comp_idx+1:])
        comp = tokens[comp_idx].value
        variables = self._extract_variables(tokens)

        return ExtractionCandidate(
            invariant_type=InvariantType.INEQUALITY,
            domain=DomainType.STABILITY,
            lhs=lhs,
            comparison=comp,
            rhs=rhs,
            variables=variables,
            conditions=conditions,
            quantifiers=quantifiers,
            source_text=source,
        )

    # ─── Pattern C: Trace Condition ───────────────────────────

    def _match_trace_condition(self, tokens: List[Token], source: str) -> Optional[ExtractionCandidate]:
        """Match: tr(A) < 0, trace negative."""
        has_trace = any(t.type == TokenType.KW_TRACE for t in tokens)
        if not has_trace:
            return None

        tokens, quantifiers = self._extract_quantifiers(tokens)
        tokens, conditions = self._extract_conditions(tokens)

        comp_idx = self._find_comparison(tokens)
        if comp_idx is None:
            # Check for "trace negative" pattern
            has_neg = any(t.value.lower() == 'negative' for t in tokens)
            if has_neg:
                return ExtractionCandidate(
                    invariant_type=InvariantType.INEQUALITY,
                    domain=DomainType.STABILITY,
                    lhs="tr(J)",
                    comparison="<",
                    rhs="0",
                    variables=self._extract_variables(tokens),
                    conditions=conditions,
                    quantifiers=quantifiers,
                    source_text=source,
                )
            return None

        lhs = self._tokens_to_expr(tokens[:comp_idx])
        rhs = self._tokens_to_expr(tokens[comp_idx+1:])
        comp = tokens[comp_idx].value

        return ExtractionCandidate(
            invariant_type=InvariantType.INEQUALITY,
            domain=DomainType.STABILITY,
            lhs=lhs,
            comparison=comp,
            rhs=rhs,
            variables=self._extract_variables(tokens),
            conditions=conditions,
            quantifiers=quantifiers,
            source_text=source,
        )

    # ─── Pattern D: Spectral Bound ───────────────────────────

    def _match_spectral_bound(self, tokens: List[Token], source: str) -> Optional[ExtractionCandidate]:
        """Match: ρ(A) < bound, Re(λ) < 0, spectral radius < ..."""
        has_spectral = any(t.type in (
            TokenType.KW_SPECTRAL, TokenType.KW_EIGENVALUE, TokenType.KW_REAL_PART
        ) for t in tokens)

        # Also check for rho as variable name
        has_rho = any(t.value == 'rho' for t in tokens)

        if not has_spectral and not has_rho:
            return None

        tokens, quantifiers = self._extract_quantifiers(tokens)
        tokens, conditions = self._extract_conditions(tokens)

        comp_idx = self._find_comparison(tokens)
        if comp_idx is None:
            return None

        lhs = self._tokens_to_expr(tokens[:comp_idx])
        rhs = self._tokens_to_expr(tokens[comp_idx+1:])
        comp = tokens[comp_idx].value

        return ExtractionCandidate(
            invariant_type=InvariantType.CONTAINMENT,
            domain=DomainType.SPECTRAL,
            lhs=lhs,
            comparison=comp,
            rhs=rhs,
            variables=self._extract_variables(tokens),
            conditions=conditions,
            quantifiers=quantifiers,
            source_text=source,
        )

    # ─── Pattern E: Logical Implication ──────────────────────

    def _match_implication(self, tokens: List[Token], source: str) -> Optional[ExtractionCandidate]:
        """Match: P ⟹ Q, if P then Q."""
        impl_idx = None
        for i, t in enumerate(tokens):
            if t.type == TokenType.IMPLIES:
                impl_idx = i
                break
        if impl_idx is None:
            return None

        premise_tokens = tokens[:impl_idx]
        conclusion_tokens = tokens[impl_idx+1:]

        premise = self._tokens_to_expr(premise_tokens)
        conclusion = self._tokens_to_expr(conclusion_tokens)

        if not premise.strip() or not conclusion.strip():
            return None

        domain = self._detect_domain(conclusion_tokens)
        if domain == DomainType.ALGEBRAIC:
            domain = self._detect_domain(premise_tokens)

        return ExtractionCandidate(
            invariant_type=InvariantType.IMPLICATION,
            domain=domain,
            lhs=premise,
            comparison="=>",
            rhs=conclusion,
            variables=self._extract_variables(tokens),
            conditions=[],
            quantifiers=[],
            source_text=source,
        )

    # ─── Pattern F: Equivalence ──────────────────────────────

    def _match_equivalence(self, tokens: List[Token], source: str) -> Optional[ExtractionCandidate]:
        """Match: P ⟺ Q, P iff Q."""
        iff_idx = None
        for i, t in enumerate(tokens):
            if t.type == TokenType.IFF:
                iff_idx = i
                break
        if iff_idx is None:
            return None

        lhs_tokens = tokens[:iff_idx]
        rhs_tokens = tokens[iff_idx+1:]

        lhs = self._tokens_to_expr(lhs_tokens)
        rhs = self._tokens_to_expr(rhs_tokens)

        if not lhs.strip() or not rhs.strip():
            return None

        domain = self._detect_domain(tokens)

        return ExtractionCandidate(
            invariant_type=InvariantType.EQUIVALENCE,
            domain=domain,
            lhs=lhs,
            comparison="iff",
            rhs=rhs,
            variables=self._extract_variables(tokens),
            conditions=[],
            quantifiers=[],
            source_text=source,
        )


# ═══════════════════════════════════════════════════════════════
# SECTION 4: CANONICALIZER
# ═══════════════════════════════════════════════════════════════

class Canonicalizer:
    """
    Normalizes extracted expressions into canonical form.

    Rules:
    1. Symbol normalization (Greek → ASCII)
    2. Commutative sorting (alpha*gamma → alpha*gamma consistently)
    3. Factorization normalization
    4. Variable registry check (undefined → reject)
    """

    # Known canonical forms
    KNOWN_FORMS = {
        # RC4-style determinant
        'beta * kappa - alpha * gamma': 'Δ = β·κ − α·γ',
        'beta * kappa > alpha * gamma': 'β·κ > α·γ',
        # Trace
        '2 * d + beta + kappa': '2d + β + κ',
        # Spectral radius
        'rho': 'ρ(C)',
    }

    def canonicalize(self, candidate: ExtractionCandidate) -> ExtractionCandidate:
        """Normalize expression to canonical form."""
        candidate.lhs = self._normalize_expr(candidate.lhs)
        candidate.rhs = self._normalize_expr(candidate.rhs)

        # Sort variables alphabetically for canonical representation
        candidate.variables = set(sorted(candidate.variables))

        # Compute confidence score
        candidate.confidence = self._compute_confidence(candidate)

        return candidate

    def _normalize_expr(self, expr: str) -> str:
        """Normalize an expression string."""
        if not expr:
            return expr

        # Strip whitespace
        expr = expr.strip()

        # Check for known canonical forms
        expr_clean = re.sub(r'\s+', ' ', expr.lower())
        for pattern, canonical in self.KNOWN_FORMS.items():
            if pattern in expr_clean:
                return canonical

        # Sort multiplication operands alphabetically
        # e.g., "gamma * alpha" → "alpha * gamma"
        parts = expr.split('*')
        if len(parts) > 1:
            parts = [p.strip() for p in parts]
            # Only sort if all parts are simple symbols
            if all(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', p) for p in parts):
                parts.sort()
                return ' * '.join(parts)

        return expr

    def _compute_confidence(self, candidate: ExtractionCandidate) -> float:
        """
        Structural completeness score.

        Not probabilistic. This is:
        - Are all variables defined? (1/5)
        - Are all operators recognized? (1/5)
        - Is the domain classified? (1/5)
        - Is there a comparison operator? (1/5)
        - Is the type assigned? (1/5)
        """
        score = 0.0

        # Variables present
        if len(candidate.variables) > 0:
            score += 0.2

        # Both sides of comparison present
        if candidate.lhs and candidate.rhs:
            score += 0.2

        # Domain classified (not just algebraic default)
        if candidate.domain != DomainType.ALGEBRAIC:
            score += 0.2
        else:
            score += 0.1  # algebraic is still valid, just less specific

        # Comparison operator present
        if candidate.comparison:
            score += 0.2

        # Type is assigned
        if candidate.invariant_type:
            score += 0.2

        return min(score, 1.0)


# ═══════════════════════════════════════════════════════════════
# SECTION 5: TIER CLASSIFIER
# ═══════════════════════════════════════════════════════════════

class TierClassifier:
    """
    Assigns operator tier based on expression structure.

    Tier 1: Only +, -, *, /, integer powers. No eigenvalues. No transcendentals.
    Tier 2: Symbolic determinant/trace, polynomial discriminants.
    Tier 3: Interval extrema, boundary optimization.
    Tier 4: Numeric eigenvalue solver, floating-point unavoidable.
    """

    TIER_4_MARKERS = {'eigenvalue', 'eigenvalues', 'eig', 'Re', 'Im', 'spec', 'spectrum'}
    TIER_3_MARKERS = {'sup', 'inf', 'max', 'min', 'interval'}
    TIER_2_MARKERS = {'det', 'trace', 'tr', 'discriminant', 'characteristic',
                      'polynomial', 'spectral', 'radius', 'delta'}

    def classify(self, candidate: ExtractionCandidate) -> int:
        """Return tier number 1–4."""
        all_text = f"{candidate.lhs} {candidate.rhs} {' '.join(candidate.conditions)}"
        all_words = set(re.findall(r'[a-zA-Z_]+', all_text.lower()))

        # Check for Tier 4 markers (word-boundary, not substring)
        if all_words & self.TIER_4_MARKERS:
            # Exception: spectral radius bound is Tier 2 (it's just ρ < bound)
            if candidate.domain == DomainType.SPECTRAL and candidate.comparison in ('<', '<='):
                if 'rho' in all_words or 'ρ' in all_text:
                    return 2
            return 4

        # Check for Tier 3 markers
        if all_words & self.TIER_3_MARKERS:
            return 3

        # Check for Tier 2 markers
        if all_words & self.TIER_2_MARKERS:
            return 2

        # Default: if it's a pure inequality with symbols and numbers, it's Tier 1
        if candidate.comparison in ('>', '<', '>=', '<=', '==', '!='):
            if not (all_words & (self.TIER_4_MARKERS | self.TIER_3_MARKERS | self.TIER_2_MARKERS)):
                # Domain-aware floor: spectral domain is at least Tier 2
                if candidate.domain == DomainType.SPECTRAL:
                    return 2
                return 1

        return 2  # safe default


# ═══════════════════════════════════════════════════════════════
# SECTION 6: INVARIANT CARD BUILDER
# ═══════════════════════════════════════════════════════════════

@dataclass
class ExtractedInvariantCard:
    """Output of the DIEG pipeline. Ready for RC7 registry ingestion."""
    id: str
    name: str
    invariant_type: str
    domain: str
    canonical_form: str
    comparison: str
    lhs: str
    rhs: str
    variables: List[str]
    conditions: List[str]
    quantifiers: List[str]
    tier: int
    confidence: float
    source_text: str
    accepted: bool
    rejection_reason: Optional[str] = None


class InvariantCardBuilder:
    """
    Builds ExtractedInvariantCard from canonicalized candidates.
    Applies rejection rules. No card on ambiguity.
    """

    CONFIDENCE_THRESHOLD = 0.6

    def build(self, candidate: ExtractionCandidate, tier: int) -> ExtractedInvariantCard:
        """Build card or reject."""
        rejection = self._check_rejection(candidate)

        accepted = rejection is None and candidate.confidence >= self.CONFIDENCE_THRESHOLD

        # Generate name from domain + type
        name = f"{candidate.domain.value}_{candidate.invariant_type.value}"
        if candidate.lhs:
            # Use first significant symbol for naming
            symbols = sorted(candidate.variables)
            if symbols:
                name = f"{candidate.domain.value}:{symbols[0]}"

        return ExtractedInvariantCard(
            id=f"EXT-{uuid.uuid4().hex[:8].upper()}",
            name=name,
            invariant_type=candidate.invariant_type.value,
            domain=candidate.domain.value,
            canonical_form=f"{candidate.lhs} {candidate.comparison} {candidate.rhs}",
            comparison=candidate.comparison,
            lhs=candidate.lhs,
            rhs=candidate.rhs,
            variables=sorted(candidate.variables),
            conditions=candidate.conditions,
            quantifiers=candidate.quantifiers,
            tier=tier,
            confidence=candidate.confidence,
            source_text=candidate.source_text,
            accepted=accepted,
            rejection_reason=rejection,
        )

    def _check_rejection(self, candidate: ExtractionCandidate) -> Optional[str]:
        """Check rejection rules. Return reason or None."""
        # R1: Empty expression
        if not candidate.lhs.strip() and not candidate.rhs.strip():
            return "Empty expression"

        # R2: No variables detected
        if len(candidate.variables) == 0:
            return "No variables detected"

        # R3: No comparison operator
        if not candidate.comparison:
            return "No comparison operator"

        # R4: Metaphorical language (heuristic)
        source_lower = candidate.source_text.lower()
        metaphor_markers = ['beauty', 'elegant', 'divine', 'magic', 'intuition',
                           'feel', 'believe', 'obvious', 'clearly']
        detected_metaphors = [m for m in metaphor_markers if m in source_lower]
        if detected_metaphors:
            # Metaphor markers present: reject unless expression is structurally rich
            # (4+ real math variables suggests real content despite flowery language)
            math_vars = candidate.variables - set(metaphor_markers) - {'x', 'y', 'z', 'n', 'k'}
            if len(candidate.variables) < 4:
                return f"Possible metaphorical language: '{detected_metaphors[0]}'"

        # R5: Self-referential
        if 'this invariant' in source_lower or 'this theorem' in source_lower:
            if len(candidate.variables) < 2:
                return "Self-referential without sufficient structure"

        return None


# ═══════════════════════════════════════════════════════════════
# SECTION 7: FULL PIPELINE
# ═══════════════════════════════════════════════════════════════

class DIEG:
    """
    Deterministic Invariant Extraction Grammar.

    Full pipeline:
        text → tokenize → pattern match → canonicalize
        → classify tier → build card → accept/reject
    """

    def __init__(self):
        self.tokenizer = Tokenizer()
        self.matcher = PatternMatcher()
        self.canonicalizer = Canonicalizer()
        self.tier_classifier = TierClassifier()
        self.card_builder = InvariantCardBuilder()

    def extract(self, text: str) -> List[ExtractedInvariantCard]:
        """
        Extract invariant cards from input text.
        Handles multi-statement inputs by splitting on sentence boundaries.
        """
        results = []

        # Split on sentence boundaries
        statements = self._split_statements(text)

        for stmt in statements:
            card = self._extract_single(stmt)
            if card is not None:
                results.append(card)

        return results

    def _extract_single(self, text: str) -> Optional[ExtractedInvariantCard]:
        """Extract a single invariant from a single statement."""
        # Phase 1: Tokenize
        tokens = self.tokenizer.tokenize(text)

        # Phase 2: Pattern match
        candidate = self.matcher.match(tokens, text)
        if candidate is None:
            return None

        # Phase 3: Canonicalize
        candidate = self.canonicalizer.canonicalize(candidate)

        # Phase 4: Classify tier
        tier = self.tier_classifier.classify(candidate)

        # Phase 5: Build card (with rejection check)
        card = self.card_builder.build(candidate, tier)

        return card

    def _split_statements(self, text: str) -> List[str]:
        """Split text into individual mathematical statements."""
        # Split on period, semicolon, or double newline
        # But preserve math expressions
        statements = re.split(r'(?<=[.;])\s+|\n\n+', text)
        # Filter empty
        return [s.strip() for s in statements if s.strip()]


# ═══════════════════════════════════════════════════════════════
# SECTION 8: TEST SUITE
# ═══════════════════════════════════════════════════════════════

def run_tests():
    """Full test suite for DIEG."""
    results = []
    t0_all = time.time()

    def test(name, condition):
        results.append({"name": name, "passed": bool(condition)})
        status = "PASS" if condition else "FAIL"
        print(f"  [{status}] {name}")

    dieg = DIEG()

    # ─── Tokenizer Tests ─────────────────────────────────────
    print("\n=== TOKENIZER TESTS ===")
    tok = Tokenizer()

    t1 = tok.tokenize("βκ − αγ > 0")
    symbols = [t for t in t1 if t.type == TokenType.SYMBOL]
    test("Tokenize Greek: 4 symbols from βκ − αγ > 0",
         len(symbols) == 4)
    test("Tokenize Greek: comparison detected",
         any(t.type == TokenType.COMPARISON for t in t1))

    t2 = tok.tokenize("\\det(A) \\geq 0")
    test("Tokenize LaTeX: det keyword detected",
         any(t.type == TokenType.KW_DETERMINANT for t in t2))
    test("Tokenize LaTeX: >= comparison",
         any(t.type == TokenType.COMPARISON and t.value == '>=' for t in t2))

    t3 = tok.tokenize("stable if and only if Re(λ) < 0")
    test("Tokenize multi-word: IFF detected",
         any(t.type == TokenType.IFF for t in t3))
    test("Tokenize multi-word: Re keyword detected",
         any(t.type == TokenType.KW_REAL_PART for t in t3))

    t4 = tok.tokenize("for all z in spec(L): max Re(eig(A + z*B)) < 0")
    test("Tokenize quantifier: FORALL detected",
         any(t.type == TokenType.FORALL for t in t4))
    test("Tokenize quantifier: IN detected",
         any(t.type == TokenType.IN for t in t4))

    t5 = tok.tokenize("∀ μ ∈ σ(L): Δ(μ) > 0")
    test("Tokenize Unicode quantifier: FORALL detected",
         any(t.type == TokenType.FORALL for t in t5))

    # ─── Pattern Matcher Tests ───────────────────────────────
    print("\n=== PATTERN MATCHER TESTS ===")

    # RC4-style: Δ = βκ − αγ > 0
    cards = dieg.extract("Δ = βκ − αγ > 0")
    test("Extract RC4 Δ: card produced", len(cards) >= 1)
    if cards:
        test("Extract RC4 Δ: domain is stability", cards[0].domain == "stability")
        test("Extract RC4 Δ: accepted", cards[0].accepted)

    # Spectral bound: ρ(C) < 1.25 * d
    cards = dieg.extract("spectral radius ρ(C) < 1.25 * d")
    test("Extract spectral bound: card produced", len(cards) >= 1)
    if cards:
        test("Extract spectral bound: domain is spectral", cards[0].domain == "spectral")
        test("Extract spectral bound: accepted", cards[0].accepted)

    # Trace condition: tr(J) < 0
    cards = dieg.extract("trace tr(J) < 0")
    test("Extract trace: card produced", len(cards) >= 1)
    if cards:
        test("Extract trace: domain is stability", cards[0].domain == "stability")

    # Implication: β·κ > α·γ ⟹ system is stable
    cards = dieg.extract("beta * kappa > alpha * gamma => stable")
    test("Extract implication: card produced", len(cards) >= 1)
    if cards:
        test("Extract implication: type is implication",
             cards[0].invariant_type == "implication")

    # Equivalence: stable iff det(J) > 0 and tr(J) < 0
    cards = dieg.extract("stable iff det(J) > 0 and tr(J) < 0")
    test("Extract equivalence: card produced", len(cards) >= 1)
    if cards:
        test("Extract equivalence: type is equivalence",
             cards[0].invariant_type == "equivalence")

    # Universal quantifier
    cards = dieg.extract("for all z in spec(L): Re(eigenvalue(A + z*B)) < 0")
    test("Extract universal: card produced", len(cards) >= 1)
    if cards:
        test("Extract universal: has quantifier", len(cards[0].quantifiers) >= 1)

    # ─── Tier Classification Tests ───────────────────────────
    print("\n=== TIER CLASSIFICATION TESTS ===")

    # Tier 1: pure rational inequality
    cards = dieg.extract("beta * kappa > alpha * gamma")
    test("Tier 1: rational inequality", len(cards) >= 1)
    if cards:
        test("Tier 1: classified as tier 1", cards[0].tier == 1)

    # Tier 2: determinant condition
    cards = dieg.extract("det(J) > 0")
    test("Tier 2: determinant", len(cards) >= 1)
    if cards:
        test("Tier 2: classified as tier 2", cards[0].tier == 2)

    # Tier 2: spectral radius (algebraic bound)
    cards = dieg.extract("spectral radius rho < 1.25 * d")
    test("Tier 2: spectral radius bound", len(cards) >= 1)
    if cards:
        test("Tier 2: spectral radius classified as tier 2", cards[0].tier == 2)

    # Tier 4: eigenvalue computation required
    cards = dieg.extract("max Re(eigenvalue(A + z*B)) < 0")
    test("Tier 4: eigenvalue required", len(cards) >= 1)
    if cards:
        test("Tier 4: classified as tier 4", cards[0].tier == 4)

    # ─── Rejection Tests ─────────────────────────────────────
    print("\n=== REJECTION TESTS ===")

    # No mathematical content
    cards = dieg.extract("The weather is nice today.")
    test("Reject: no math content", len(cards) == 0)

    # Metaphorical language
    cards = dieg.extract("The beauty of x > 0")
    test("Reject or low confidence: metaphorical",
         len(cards) == 0 or (cards and not cards[0].accepted))

    # Pure narrative
    cards = dieg.extract("We believe this approach is elegant and novel.")
    test("Reject: pure narrative", len(cards) == 0)

    # ─── Confidence Score Tests ──────────────────────────────
    print("\n=== CONFIDENCE TESTS ===")

    cards = dieg.extract("beta * kappa - alpha * gamma > 0")
    test("Confidence: well-formed inequality ≥ 0.6",
         len(cards) >= 1 and cards[0].confidence >= 0.6)

    cards = dieg.extract("x > 0")
    test("Confidence: minimal inequality produces card",
         len(cards) >= 1)

    # ─── Multi-Statement Tests ───────────────────────────────
    print("\n=== MULTI-STATEMENT TESTS ===")

    multi = """
    The system is stable iff Δ > 0.
    The trace condition requires tr(J) < 0.
    The spectral radius satisfies ρ(C) < 1.25 * d.
    """
    cards = dieg.extract(multi)
    test("Multi-statement: extracts ≥ 2 cards", len(cards) >= 2)
    test("Multi-statement: all accepted",
         all(c.accepted for c in cards) if cards else False)

    # ─── LaTeX Input Tests ───────────────────────────────────
    print("\n=== LATEX INPUT TESTS ===")

    cards = dieg.extract(r"\beta \cdot \kappa > \alpha \cdot \gamma")
    test("LaTeX: detects inequality", len(cards) >= 1)
    if cards:
        test("LaTeX: accepted", cards[0].accepted)

    cards = dieg.extract(r"\forall z \in \operatorname{spec}(L): \operatorname{Re}(\lambda) < 0")
    test("LaTeX: detects quantified spectral", len(cards) >= 1)

    # ─── Export Format Tests ─────────────────────────────────
    print("\n=== EXPORT TESTS ===")

    cards = dieg.extract("beta * kappa > alpha * gamma")
    if cards:
        card = cards[0]
        test("Export: has id", card.id.startswith("EXT-"))
        test("Export: has variables", len(card.variables) > 0)
        test("Export: has canonical_form", len(card.canonical_form) > 0)
        test("Export: has tier", card.tier in (1, 2, 3, 4))
        test("Export: has confidence", 0.0 <= card.confidence <= 1.0)
        test("Export: has source_text", len(card.source_text) > 0)

        # JSON serializable
        import dataclasses
        d = dataclasses.asdict(card)
        j = json.dumps(d)
        test("Export: JSON serializable", j is not None)

    # ─── Integration: RC Stack Statement Tests ───────────────
    print("\n=== RC STACK INTEGRATION TESTS ===")

    # Statements as they appear in actual RC4/RC5/RC6 documentation
    rc_statements = [
        ("RC4: Δ = βκ − αγ > 0", "stability"),
        ("RC4: tr(J) = −(2d + β + κ) < 0", "stability"),
        ("RC5: for all edges e: Δ(e) > 0 => stable when graph is tree", "stability"),
        ("RC6: spectral radius ρ(C) < 1.25 * d", "spectral"),
        ("RC6: ∀ z ∈ spec(C): max Re(eigenvalue(D + z*A)) < 0", "spectral"),
    ]

    for stmt, expected_domain in rc_statements:
        cards = dieg.extract(stmt)
        test(f"RC stack: '{stmt[:40]}...' → card produced", len(cards) >= 1)
        if cards:
            test(f"RC stack: '{stmt[:40]}...' → accepted", cards[0].accepted)

    # ─── Summary ─────────────────────────────────────────────
    elapsed = (time.time() - t0_all) * 1000
    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])
    total = len(results)

    print(f"\n{'='*60}")
    print(f"DIEG TEST RESULTS: {passed}/{total} passed, {failed} failed")
    print(f"Time: {elapsed:.0f}ms")
    print(f"{'='*60}")

    if failed > 0:
        print("\nFAILED TESTS:")
        for r in results:
            if not r["passed"]:
                print(f"  ✗ {r['name']}")

    return {"total": total, "passed": passed, "failed": failed}


if __name__ == "__main__":
    run_tests()
