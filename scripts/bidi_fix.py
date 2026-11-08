#!/usr/bin/env python3
"""Make Arabic Markdown with English terms and math display in the right order.

Reads a file (or stdin), converts powers to real symbols, starts mixed lines in
the right direction, isolates equations, and separates soft-wrapped lines.
Code blocks, inline code contents, links, and URLs are never altered.
Running it twice gives the same result.
"""
import argparse
import re
import sys
import unicodedata
from pathlib import Path

RLM, LRI, PDI = "‏", "⁦", "⁩"
ARABIC = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")
SUPERSCRIPTS = dict(zip("0123456789+-=()nixkm", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱˣᵏᵐ"))
SUP_CHARS = "".join(SUPERSCRIPTS.values())

FENCE = re.compile(r"^\s*(```|~~~|\$\$)")
PREFIX = re.compile(r"^(\s*(?:>\s*)*(?:#{1,6}\s+|[-*+]\s+|\d+[.)]\s+)?)(.*)$", re.S)
BLOCK_START = re.compile(r"^\s*(?:>|#{1,6}\s|[-*+]\s|\d+[.)]\s|\||(?:-{3,}|\*{3,}|_{3,})\s*$)")
PROTECTED = re.compile(r"(`[^`\n]+`|\[[^\]\n]*\]\([^)\n]*\)|https?://[^\s)]+|\$[^$\n]+\$)")
MATH_CHAR = rf"0-9A-Za-z{SUP_CHARS}=+\-−–×÷/<>≤≥≠≈√∑%^().,"
MATH_RUN = re.compile(rf"[{MATH_CHAR}](?:[{MATH_CHAR} ]*[{MATH_CHAR}])?")
NEEDS_ISOLATE = re.compile(r"[=+×÷<>≤≥≠≈^]|\d\s*/\s*\d|\d\s+[-−–]\s+\d|^[-−]\d|\d,\s+\d")
ARABIC_POWER = re.compile(r"(?<![\w])(\d+|[A-Za-z])\s+(?:أس|اس)\s+(\d+|[nixkm])(?![\w])")
WORD_POWER = re.compile(r"(?:\d+|[A-Za-z])\s+(?:أس|اس)\s+[؀-ۿ]+(?:\s+[؀-ۿ]+)?")
CARET_POWER = re.compile(r"([0-9A-Za-z)])\s*\^\s*(?:\{([^{}\s]+)\}|\(([^()\s]+)\)|([0-9]+|[nixkm])(?![A-Za-z0-9]))")


def superscript(text):
    return "".join(SUPERSCRIPTS[c] for c in text)


def convert_powers(text):
    def caret(match):
        braces, parens, plain = match.group(2), match.group(3), match.group(4)
        exponent = braces or parens or plain
        if any(c not in SUPERSCRIPTS for c in exponent):
            return match.group(0)
        return match.group(1) + superscript(exponent)

    text = ARABIC_POWER.sub(lambda m: m.group(1) + superscript(m.group(2)), text)
    text = CARET_POWER.sub(caret, text)
    text = re.sub(r"(?<=[\w)]) \* (?=[\w(])", " × ", text)
    for ascii_op, symbol in (("<=", "≤"), (">=", "≥"), ("!=", "≠")):
        text = text.replace(ascii_op, symbol)
    return text


def balanced(text):
    depth = 0
    for char in text:
        depth += (char == "(") - (char == ")")
        if depth < 0:
            return False
    return depth == 0


def needs_isolate(text):
    return bool(re.search(r"\d", text) and NEEDS_ISOLATE.search(text))


def isolate_run(match):
    run = match.group(0)
    string, start = match.string, match.start()
    if start and string[start - 1] == LRI:
        return run
    core = run.rstrip(".,")
    while core.endswith(")") and not balanced(core):
        core = core[:-1]
    dangling_operator = re.match(r"[=+×÷<>≤≥≠≈^/]", core) or re.search(r"[=+\-−–×÷<>≤≥≠≈^/]$", core)
    if not core or dangling_operator or not balanced(core) or not needs_isolate(core):
        return run
    return f"{LRI}{core}{PDI}{run[len(core):]}"


def isolate_math(text):
    parts = PROTECTED.split(text)
    for index, part in enumerate(parts):
        if index % 2 == 0:
            parts[index] = MATH_RUN.sub(isolate_run, convert_powers(part))
            continue
        previous = parts[index - 1]
        if part.startswith("`") and needs_isolate(part[1:-1]) and not previous.endswith(LRI):
            parts[index] = f"{LRI}{part}{PDI}"
    return "".join(parts)


def first_strong(text):
    depth = 0
    for char in text:
        if char == LRI:
            depth += 1
        elif char == PDI:
            depth = max(depth - 1, 0)
        elif depth == 0:
            direction = unicodedata.bidirectional(char)
            if direction in ("L", "R", "AL"):
                return "L" if direction == "L" else "R"
    return None


def set_direction(text):
    stripped = text.lstrip()
    if not ARABIC.search(text) or stripped.startswith(RLM):
        return text
    if first_strong(text) == "L" or re.match(r"[*_]*" + LRI, stripped):
        lead = len(text) - len(stripped)
        return f"{text[:lead]}{RLM}{stripped}"
    return text


def fix_table_row(line):
    cells = re.split(r"(?<!\\)\|", line)
    if all(re.fullmatch(r"\s*:?-*:?\s*", cell) for cell in cells):
        return line
    fixed = []
    for cell in cells:
        if ARABIC.search(cell):
            cell = set_direction(isolate_math(cell))
        fixed.append(cell)
    return "|".join(fixed)


def fix_line(line):
    if line.lstrip().startswith("|"):
        return fix_table_row(line)
    if not ARABIC.search(line):
        return line
    prefix, content = PREFIX.match(line).groups()
    return prefix + set_direction(isolate_math(content))


def is_plain(line):
    return bool(line.strip()) and not line.startswith(("    ", "\t")) and not BLOCK_START.match(line)


def fix_text(text):
    output, warnings = [], []
    fence = None
    previous_source = ""
    lines = text.split("\n")
    in_front_matter = bool(lines) and lines[0].strip() == "---"
    for number, line in enumerate(lines, 1):
        if in_front_matter:
            output.append(line)
            if number > 1 and line.strip() == "---":
                in_front_matter = False
            continue
        marker = FENCE.match(line)
        if fence:
            output.append(line)
            if marker and marker.group(1) == fence:
                fence = None
            previous_source = ""
            continue
        if marker:
            fence = marker.group(1)
            output.append(line)
            previous_source = ""
            continue
        for phrase in WORD_POWER.findall(line):
            if not ARABIC_POWER.search(phrase):
                warnings.append(f"line {number}: rewrite with a symbol such as 2ⁿ: {phrase}")
        mixed = ARABIC.search(line) or ARABIC.search(previous_source)
        if is_plain(line) and is_plain(previous_source) and mixed:
            output.append("")
        output.append(fix_line(line))
        previous_source = line
    return "\n".join(output), warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", nargs="?", help="file to read (default: stdin)")
    parser.add_argument("-o", "--output", help="file to write (default: stdout)")
    parser.add_argument("--in-place", action="store_true", help="overwrite the input file")
    parser.add_argument("--check", action="store_true", help="report only; exit 1 if changes are needed")
    args = parser.parse_args()
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", newline="\n" if stream is sys.stdout else None)
    if args.in_place and not args.input:
        parser.error("--in-place needs an input file")

    source = Path(args.input).read_text(encoding="utf-8-sig") if args.input else sys.stdin.read()
    newline = "\r\n" if "\r\n" in source else "\n"
    fixed, warnings = fix_text(source.replace("\r\n", "\n"))
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    changed = fixed != source.replace("\r\n", "\n")

    if args.check:
        print("needs fixing" if changed else "already fine", file=sys.stderr)
        return int(changed or bool(warnings))
    fixed = fixed.replace("\n", newline)
    target = args.input if args.in_place else args.output
    if target:
        Path(target).write_text(fixed, encoding="utf-8", newline="")
    else:
        sys.stdout.write(fixed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
