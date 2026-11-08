---
name: arabic-mixed-text
description: Keeps Arabic explanations readable when they contain English technical terms, numbers, vectors, or math. Use this whenever you reply or write in Arabic (including Egyptian dialect) and the text includes any English term, code name, number list, equation, or power such as 2^3, even if the user does not mention formatting. Also use it when the user complains that Arabic and English are scrambled, reversed, or out of order, asks to keep the explanation in Arabic with English terms, or wants math written with real symbols.
---

# Arabic text with English terms and math

## Why text gets scrambled

Most chat apps pick each paragraph's direction from its first letter. A paragraph that opens with an English word becomes left-to-right, and its Arabic phrases then appear in the wrong order. Inside a right-to-left paragraph the opposite happens: separate numbers and operators get reversed, so `2³ = 8` shows as `8 = 2³` and `(2, 1, 1, 0)` shows as `(0, 1, 1, 2)`.

The layout below prevents both problems using ordinary characters, so it works in chat where nothing can post-process your reply.

## Language

Write the explanation in Arabic, in the user's dialect. Keep technical terms in English (`Snowflake`, `join`, `vector`). Do not translate a term the user's material leaves in English. Attach Arabic to terms the natural way: `الـ Star`, `الـ joins`.

## Layout rules

1. **Start every paragraph, list item, heading, and mixed table cell with an Arabic word.** This sets the direction correctly.
   - Wrong: `Document A: "coach team"`
   - Right: `المستند A: "coach team"`
   - Wrong: `Storage` as a label
   - Right: `**مقارنة الـ Storage**`
2. **Leave a blank line between lines.** A single line break keeps both lines in one paragraph, so an English first line flips the Arabic line after it. Put a label and its explanation on one line, or separate them with a blank line.
3. **Put each equation on its own line, in a code block.** Introduce it with an Arabic sentence, then explain it in the next one.
4. **Use real math symbols**, never words like "أس" or caret notation.
   - Powers: `2³`, `2ⁿ`, `xⁿ⁺¹`
   - Others: `×`, `÷`, `≤`, `≥`, `≠`, `√`, `∑`, `≈`
   - When the exponent is a concept, name it with a symbol first and define it after the block in Arabic, as in the example.
5. **Write inline number lists without spaces after commas**, such as `(2,1,1,0)`. A comma between digits keeps the list in order. For anything longer, use a code block.
6. **Keep these out of running Arabic sentences**, because they reorder or lose their sign: `5 - 3`, `-5`, arrows such as `A → B`. Put them in a code block. Latin words, single numbers, `50%`, and `team = 2` are safe inline.

## Example

Before:

```text
Performance
الـ Snowflake أبطأ، لأن فيه joins كتير.

عدد المكعبات الملخصة = 2 أس عدد الأبعاد. يعني 2 أس 3 = 8.

Document A: الـ vector هو (2, 1, 1, 0)
```

After:

````markdown
**مقارنة الـ Performance**

الـ Snowflake أبطأ، لأن فيه joins كتير.

عدد المكعبات الملخصة بيتحسب بالقانون ده:

```text
Cuboids = 2ⁿ
```

حيث n هو عدد الأبعاد. وعندنا 3 أبعاد، فالناتج:

```text
2³ = 8
```

المستند A الـ vector بتاعه هو (2,1,1,0).
````

## Files and existing text

Chat replies rely on the rules above. For a Markdown or text file, or text the user wants repaired, also run the bundled fixer, which adds invisible direction marks and converts powers:

```bash
python scripts/bidi_fix.py input.md -o output.md
```

Resolve `scripts/` relative to this skill's folder. Use `--in-place` to overwrite the input, only when the user wants that, or `--check` to report problems without changing anything. Warnings point to phrases it cannot convert alone, such as `2 أس عدد الأبعاد`, so rewrite those by hand using rule 4.
