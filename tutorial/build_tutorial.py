"""Build the Y13 ADT tutorial as a Colab notebook (.ipynb) and a PDF.

Usage: python build_tutorial.py <project_dir> <out_dir> <work_dir>
"""
import base64, contextlib, html, io, json, os, subprocess, sys

import markdown
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

PROJECT, OUT, WORK = (os.path.abspath(p) for p in sys.argv[1:4])
os.makedirs(OUT, exist_ok=True)
os.makedirs(WORK, exist_ok=True)


def src(name):
    with open(os.path.join(PROJECT, name), encoding="utf-8") as f:
        return f.read().strip() + "\n"


# --------------------------------------------------------------------------
# Cell model
#   md(text)                      markdown cell (notebook + PDF)
#   code(text, run=True)          code cell; run=False -> shown but not executed
#   fig(fn, caption)              SVG diagram drawn from the live state
#   exercise(id, title, task, skeleton, tests, solution)
# --------------------------------------------------------------------------
CELLS = []
def md(text): CELLS.append({"kind": "md", "text": text.strip("\n")})
def code(text, run=True): CELLS.append({"kind": "code", "text": text.strip("\n"), "run": run})
def fig(fn, caption): CELLS.append({"kind": "fig", "fn": fn, "caption": caption})
def exercise(eid, title, task, skeleton, tests, solution):
    CELLS.append({"kind": "ex", "id": eid, "title": title, "task": task.strip("\n"),
                  "skeleton": skeleton.strip("\n"), "tests": tests.strip("\n"),
                  "solution": solution.strip("\n")})
def trace(tid, title, question, answer_md, answer_code):
    CELLS.append({"kind": "trace", "id": tid, "title": title, "question": question.strip("\n"),
                  "answer_md": answer_md.strip("\n"), "answer_code": answer_code.strip("\n")})


# --------------------------------------------------------------------------
# SVG diagrams
# --------------------------------------------------------------------------
FILL, STROKE, EMPTY, GHOST, TEXT, ACCENT, FREE = (
    "#dbeafe", "#1e3a8a", "#f1f5f9", "#94a3b8", "#0f172a", "#2563eb", "#fef3c7")


def _svg(w, h, body):
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}' "
            f"font-family='Segoe UI, Helvetica, Arial, sans-serif' font-size='14'>"
            f"<defs><marker id='ah' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='7' markerHeight='7' "
            f"orient='auto-start-reverse'><path d='M0,0 L10,5 L0,10 z' fill='#334155'/></marker></defs>"
            f"<rect width='100%' height='100%' fill='white'/>{body}</svg>")


def _rect(x, y, w, h, fill, stroke=STROKE, dash=False):
    d = " stroke-dasharray='4 3'" if dash else ""
    return f"<rect x='{x}' y='{y}' width='{w}' height='{h}' fill='{fill}' stroke='{stroke}' stroke-width='1.5'{d}/>"


def _text(x, y, s, anchor="middle", color=TEXT, size=14, weight="normal", style="normal", mono=False):
    fam = " font-family='Consolas, Menlo, monospace'" if mono else ""
    return (f"<text x='{x}' y='{y}' text-anchor='{anchor}' fill='{color}' font-size='{size}' "
            f"font-weight='{weight}' font-style='{style}'{fam}>{html.escape(str(s))}</text>")


def _arrow(x1, y1, x2, y2, color="#334155", dash=False):
    d = " stroke-dasharray='5 4'" if dash else ""
    return (f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' stroke='{color}' stroke-width='1.8'{d} "
            f"marker-end='url(#ah)'/>")


def svg_stack(ns, n=6):
    data, top = ns["sData"], ns["sTop"]
    cw, ch, x0, y0 = 90, 34, 70, 34
    body = _text(x0 + cw / 2, y0 - 12, "sData", weight="bold")
    for k, i in enumerate(range(n - 1, -1, -1)):
        y = y0 + k * ch
        used = i <= top
        body += _rect(x0, y, cw, ch, FILL if used else EMPTY)
        body += _text(x0 - 10, y + ch / 2 + 5, i, anchor="end", color=GHOST, mono=True)
        if data[i] != "-":
            body += _text(x0 + cw / 2, y + ch / 2 + 5, data[i], color=TEXT if used else GHOST,
                          style="normal" if used else "italic", mono=True)
        if i == top:
            body += _arrow(x0 + cw + 55, y + ch / 2, x0 + cw + 5, y + ch / 2)
            body += _text(x0 + cw + 60, y + ch / 2 + 5, f"sTop = {top}", anchor="start", weight="bold", color=ACCENT)
    if top == -1:
        y = y0 + n * ch + 14
        body += _text(x0 + cw + 60, y, "sTop = -1 (empty)", anchor="start", weight="bold", color=ACCENT)
    return _svg(300, y0 + n * ch + 26, body)


def svg_queue(ns):
    data, front, rear, count, size = ns["qData"], ns["qFront"], ns["qRear"], ns["qCount"], ns["qSize"]
    cw, ch, x0, y0 = 70, 40, 40, 74
    occupied = {(front + k) % size for k in range(count)}
    xr = x0 + size * cw
    body = (f"<path d='M {xr - cw / 2},{y0 - 24} C {xr - cw / 2},{2} {x0 + cw / 2},{2} {x0 + cw / 2},{y0 - 26}' "
            f"fill='none' stroke='{GHOST}' stroke-width='1.5' stroke-dasharray='5 4' marker-end='url(#ah)'/>")
    body += _text((x0 + xr) / 2, 42, "wraps around: (index + 1) % qSize", color=GHOST, size=12)
    for i in range(size):
        x = x0 + i * cw
        body += _text(x + cw / 2, y0 - 8, i, color=GHOST, mono=True)
        body += _rect(x, y0, cw, ch, FILL if i in occupied else EMPTY)
        if data[i] != "-":
            body += _text(x + cw / 2, y0 + ch / 2 + 5, data[i], mono=True)
    yb = y0 + ch
    fx = x0 + front * cw + cw / 2
    rx = x0 + rear * cw + cw / 2
    if front == rear:
        fx, rx = fx - 14, rx + 14
    body += _arrow(fx, yb + 34, fx, yb + 4, color=ACCENT) + _text(fx, yb + 50, "qFront", color=ACCENT, weight="bold")
    if rear != -1:
        body += _arrow(rx, yb + 34, rx, yb + 4, color="#b45309") + _text(rx, yb + 66, "qRear", color="#b45309", weight="bold")
    body += _text(xr + 20, y0 + ch / 2 + 5, f"qCount = {count}", anchor="start", weight="bold")
    return _svg(xr + 140, yb + 80, body)


def svg_linked(ns, max_free=3):
    data, links, start, heap = ns["lData"], ns["lLinks"], ns["lStart"], ns["lHeap"]
    dw, lw, h, gap = 50, 40, 36, 46

    def row(first, y, label, fill, limit=None):
        out = _rect(10, y, 72, h, "white", dash=True) + _text(46, y + 15, label, size=12, weight="bold")
        out += _text(46, y + 30, first, size=12, mono=True)
        x, cur, shown = 82 + gap, first, 0
        if cur != -1:
            out += _arrow(82, y + h / 2, x - 3, y + h / 2)
        else:
            out += _text(96, y + h / 2 + 5, "(none)", anchor="start", color=GHOST, size=12)
        while cur != -1:
            if limit is not None and shown == limit:
                out += _text(x + 4, y + h / 2 + 5, "…", anchor="start", color=GHOST, size=20)
                x += 30
                break
            out += _text(x + (dw + lw) / 2, y - 6, f"[{cur}]", color=GHOST, size=12, mono=True)
            out += _rect(x, y, dw, h, fill) + _rect(x + dw, y, lw, h, "white")
            out += _text(x + dw / 2, y + h / 2 + 5, data[cur], mono=True)
            out += _text(x + dw + lw / 2, y + h / 2 + 5, links[cur], size=12, mono=True, color="#475569")
            nxt = links[cur]
            if nxt != -1 and not (limit is not None and shown + 1 == limit):
                out += _arrow(x + dw + lw / 2 + 8, y + h / 2, x + dw + lw + gap - 3, y + h / 2)
            x += dw + lw + gap
            cur, shown = nxt, shown + 1
        return out, x

    r1, w1 = row(start, 30, "lStart", FILL)
    r2, w2 = row(heap, 110, "lHeap", FREE, limit=max_free)
    body = r1 + r2
    body += _text(10, 100, "free list (unused nodes)", anchor="start", color="#b45309", size=12)
    return _svg(max(w1, w2, 360) + 10, 160, body)


def svg_tree(ns):
    data, left, right, root = ns["bData"], ns["bLeft"], ns["bRight"], ns["bRoot"]
    pos, depth = {}, {}

    def walk(node, d):
        if node == -1:
            return
        walk(left[node], d + 1)
        pos[node] = len(pos)
        depth[node] = d
        walk(right[node], d + 1)
    walk(root, 0)
    sx, sy, x0, y0, r = 58, 70, 40, 46, 20
    xy = {nd: (x0 + pos[nd] * sx, y0 + depth[nd] * sy) for nd in pos}
    body = ""
    for nd, (x, y) in xy.items():
        for child in (left[nd], right[nd]):
            if child != -1:
                cx, cy = xy[child]
                body += f"<line x1='{x}' y1='{y}' x2='{cx}' y2='{cy}' stroke='{STROKE}' stroke-width='1.5'/>"
    for nd, (x, y) in xy.items():
        body += f"<circle cx='{x}' cy='{y}' r='{r}' fill='{FILL}' stroke='{STROKE}' stroke-width='1.5'/>"
        body += _text(x, y + 5, data[nd], mono=True, weight="bold")
        body += _text(x + r + 3, y - r + 4, f"[{nd}]", anchor="start", color=GHOST, size=11, mono=True)
    rx, ry = xy[root]
    body += _text(rx, 16, f"bRoot = {root}", color=ACCENT, weight="bold", size=13)
    w = x0 * 2 + max(len(pos) - 1, 1) * sx + 20
    h = y0 + max(depth.values()) * sy + 36
    return _svg(max(w, 160), h, body)


# --------------------------------------------------------------------------
# CONTENT
# --------------------------------------------------------------------------
md("""
# Abstract Data Types in Python
### Y13 Computer Science — Stacks, Queues, Linked Lists and Binary Trees

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mrpiay/Y13_ADTs/blob/main/tutorial/ADTs_Y13_Tutorial.ipynb)
&nbsp; Code and PDF: [github.com/mrpiay/Y13_ADTs](https://github.com/mrpiay/Y13_ADTs)

This tutorial uses four small Python programs — `stack.py`, `queue.py`, `linked_list.py` and `binary_tree.py` — to show how the classic **Abstract Data Types (ADTs)** are built from nothing more than **arrays** and **integer pointers**.

**By the end you should be able to:**

- explain what an ADT is and why we separate *what* it does from *how* it is built;
- implement a **stack**, a **circular queue**, a **linked list** and a **binary search tree** using arrays;
- explain how a **free list** (called the *heap* in this code) recycles unused nodes;
- **trace** the contents of the arrays and pointers after a sequence of operations — a very common exam question;
- write new operations (search, count, reverse, traversals…) on top of an existing ADT.

**How to use it**

1. Run the cells **in order** (in Colab: *Runtime → Run all*, or `Shift + Enter` one cell at a time).
2. Each section contains ✏️ **exercises**: write your code in the empty cell, then run the 🧪 test cell below it.
3. Solutions are hidden in collapsed ✅ cells — try properly before you peek!
""")

code('''
# Setup: a tiny helper used by the test cells in this tutorial.
def check(label, got, expected):
    if got == expected:
        print(f"✅ {label}")
    else:
        print(f"❌ {label}: expected {expected!r}, got {got!r}")
''')

# ---------------------------------------------------------------- 1. ADTs
md("""
# 1. What is an Abstract Data Type?

An **Abstract Data Type (ADT)** is a collection of data together with a set of **operations** on that data. It is defined by **what it does**, not by **how it is built**.

| | **The ADT (abstract view)** | **The implementation (concrete view)** |
|---|---|---|
| Question it answers | *What* can I do with it? | *How* is it stored and coded? |
| Stack example | `push`, `pop`, `peek`, `isEmpty`, `isFull` | an array `sData` and an integer `sTop` |
| Who cares? | the programmer **using** the stack | the programmer **writing** the stack |

Because the user only depends on the operations, the implementation can be changed (array → linked nodes, Python list → database…) **without changing any code that uses it**. This is **abstraction** and **encapsulation**.

### Why build ADTs with arrays?

Python already has lists, `collections.deque` and so on — but in the exam you are expected to build these structures from a **fixed-size array** and **integer pointers**, exactly as you would in a language without dynamic structures. That is precisely what our four files do.

### Conventions used in all four files

| Convention | Meaning |
|---|---|
| Prefixes `s`, `q`, `l`, `b` | stack, queue, linked list, binary tree — so names never clash |
| `xInit()` | creates the arrays and resets the pointers. **Always call it first.** |
| `xEmpty()` / `xFull()` | Boolean checks used before removing / adding |
| A **pointer** | just an **index** into an array (an integer) |
| `-1` | the **null pointer**: "points nowhere" (empty, end of list, no child) |
| `'-'` | placeholder meaning "this slot holds no data" |
| `global` | the functions change variables created in `xInit()`, so they must declare them `global` |

> 💡 **Key idea:** In every structure below, the "boxes and arrows" you draw on paper are really just **numbers stored in arrays**. An arrow from node 3 to node 7 simply means "`links[3]` contains `7`".
""")

# ---------------------------------------------------------------- 2. Stack
md("""
# 2. The Stack (LIFO)

A **stack** is a **Last In, First Out** structure: the last item added is the first one removed — like a pile of plates.

| Operation | Function | What it does |
|---|---|---|
| push | `sPush(value)` | add an item on top |
| pop | `sPop()` | remove **and return** the top item |
| peek | `sPeek()` | return the top item **without** removing it |
| isEmpty / isFull | `sEmpty()` / `sFull()` | check before popping / pushing |

**Where stacks are used:** *undo* in editors, the browser *back* button, the **call stack** that stores return addresses for subroutines (and recursion), evaluating Reverse Polish expressions, checking brackets, backtracking (mazes).

### Implementation with an array

| Variable | Role |
|---|---|
| `sSize` | maximum number of items (40) |
| `sData` | the array holding the items |
| `sTop` | index of the **top** item; `-1` means the stack is empty |

- **push:** check not full → `sTop = sTop + 1` → store the value at `sData[sTop]`
- **pop:** check not empty → read `sData[sTop]` → `sTop = sTop - 1`

Here is `stack.py`, unchanged. Run it to define the functions:
""")
code(src("stack.py"))

md("""
To *see* what happens inside the array we add a small helper that prints the first slots, top first, and marks where `sTop` points:
""")
code('''
def sShow(n=6):
    """Show the bottom n slots of the stack array, highest index first."""
    print("index | sData")
    print("------+------")
    for i in range(n - 1, -1, -1):
        marker = "  <-- sTop" if i == sTop else ""
        print(f"{i:>5} | {str(sData[i]):<5}{marker}")
    print("sTop =", sTop)
''')
md("### Trying it out")
code('''
sInit()
for value in ["A", "B", "C", "D"]:
    sPush(value)
sShow()
''')
code('''
print("Popped:", sPop())
print("Popped:", sPop())
print("Peek:  ", sPeek())
sShow()
''')
fig(svg_stack, "The stack after two pops. C and D are still physically in the array, but they are above sTop, so they are no longer part of the stack.")
md("""
> ⚠️ **Common misconception:** `sPop()` does **not** delete anything from the array — it only moves `sTop` down. `C` and `D` are still in `sData[2]` and `sData[3]`, but anything **above `sTop`** is treated as garbage and will be overwritten by the next push. Examiners love asking for the array contents after some pops!

### Underflow and overflow

- **Underflow:** popping from an empty stack.
- **Overflow:** pushing onto a full stack.
""")
code('''
sInit()
result = sPop()                 # underflow
print("sPop() returned:", result)

for i in range(sSize + 1):     # one push too many -> overflow
    sPush(i)
print("sTop =", sTop, "| sFull() =", sFull())
''')
md("""
Notice that `sPop()` on an empty stack prints a message and then returns `None` (there is no `return` on that path). Code that uses the stack should therefore **check `sEmpty()` before popping**.

> 📝 **Efficiency:** push, pop and peek are all **O(1)** — they take the same time however many items the stack holds.

**Quick check** — answer in your head:
1. Why does `sTop` start at `-1` and not `0`?
2. What is the value of `sTop` when the stack is full?
3. Why does `sPush` need `global sTop` but `sEmpty` does not?
""")

exercise("E1", "Reverse a string with a stack",
"""
Write `reverseString(string)` that returns the string reversed, **using the stack ADT** (`sInit`, `sPush`, `sPop`, `sEmpty`). Do **not** use slicing like `string[::-1]`.

*Hint:* push every character, then pop until the stack is empty.
""",
'''
def reverseString(string):
    # Your code here
    pass
''',
'''
check("reverseString('hello')", reverseString("hello"), "olleh")
check("reverseString('')", reverseString(""), "")
check("reverseString('Y13')", reverseString("Y13"), "31Y")
''',
'''
def reverseString(string):
    sInit()                      # start with an empty stack
    for char in string:
        sPush(char)              # push every character
    reversedString = ""
    while not sEmpty():
        reversedString += sPop() # the last character in comes out first
    return reversedString
''')

exercise("E2", "Balanced brackets",
"""
A classic use of a stack. Write `isBalanced(expression)` that returns `True` if every bracket in the expression is closed in the correct order. It must handle **three** kinds of bracket: `()`, `[]` and `{}`.

- `"{[()]}"` → `True` &nbsp;&nbsp; `"([)]"` → `False` &nbsp;&nbsp; `"(()"` → `False`

*Hint:* push every opening bracket. When you meet a closing bracket, the stack must not be empty **and** the popped bracket must be the matching opener. At the end the stack must be empty.
""",
'''
def isBalanced(expression):
    # Your code here
    pass
''',
'''
check("(())", isBalanced("(())"), True)
check("(()", isBalanced("(()"), False)
check(")(", isBalanced(")("), False)
check("{[()]}", isBalanced("{[()]}"), True)
check("([)]", isBalanced("([)]"), False)
check("a*(b+c[i])", isBalanced("a*(b+c[i])"), True)
''',
'''
def isBalanced(expression):
    pairs = {")": "(", "]": "[", "}": "{"}   # closing bracket -> its opener
    sInit()
    for char in expression:
        if char in "([{":
            sPush(char)
        elif char in pairs:
            # nothing to match, or the wrong kind of bracket
            if sEmpty() or sPop() != pairs[char]:
                return False
    return sEmpty()   # any brackets left open?
''')

# ---------------------------------------------------------------- 3. Queue
md("""
# 3. The Circular Queue (FIFO)

A **queue** is a **First In, First Out** structure: items leave in the same order they arrived — like a queue at the canteen.

| Operation | Function | What it does |
|---|---|---|
| enqueue | `qAdd(value)` | add an item at the **rear** |
| dequeue | `qRemove()` | remove the item at the **front** |
| isEmpty / isFull | `qEmpty()` / `qFull()` | check before removing / adding |

**Where queues are used:** printer spools, keyboard buffers, processes waiting for the CPU, network packets, breadth-first search.

### Why *circular*?

In a simple **linear** queue the front pointer keeps moving to the right as items are removed. The slots behind it are wasted, and soon the queue reports "full" even though most of the array is empty.

A **circular queue** fixes this: when a pointer reaches the end of the array it **wraps around to index 0**. The trick is the **modulo** operator `%`:

```
next = (current + 1) % qSize        # with qSize = 4:  0 → 1 → 2 → 3 → 0 → 1 …
```

### Implementation with an array

| Variable | Role |
|---|---|
| `qSize` | maximum number of items (only **4**, so we can see the wrap-around) |
| `qData` | the array holding the items |
| `qFront` | index of the item at the **front** (next to leave) |
| `qRear` | index of the item at the **rear** (last to arrive); starts at `-1` |
| `qCount` | how many items are in the queue |

> 💡 **Why keep `qCount`?** In a circular queue, `qFront` and `qRear` alone can look the same when the queue is empty and when it is full. Counting the items makes `qEmpty()` and `qFull()` trivial and unambiguous.

Here is `queue.py`, unchanged:
""")
code(src("queue.py"))
code('''
def qShow():
    """Show the queue array together with its pointers and counter."""
    print("index :", " ".join(f"{i:>4}" for i in range(qSize)))
    print("qData :", " ".join(f"{str(x):>4}" for x in qData))
    print(f"qFront = {qFront}, qRear = {qRear}, qCount = {qCount}")
''')
md("### Trying it out — watch the wrap-around")
code('''
qInit()
for value in [10, 20, 30]:
    qAdd(value)
qShow()
''')
code('''
qRemove()
qRemove()
qShow()
''')
code('''
for value in [40, 50, 60]:   # the rear pointer goes 3 -> 0 -> 1
    qAdd(value)
qShow()
print()
qAdd(70)                     # the queue is now full
print()
print("Queue in order, front to rear:")
qPrint()
''')
fig(svg_queue, "The circular queue after the wrap-around. The logical order (30, 40, 50, 60) is not the same as the physical order in the array.")
md("""
> ⚠️ **Notice:** physically the array holds `50 60 30 40`, but the queue order is `30 40 50 60`, starting from `qFront`. Always read a circular queue **from `qFront`, wrapping round**.

Two things to notice in `qRemove()`:
- unlike `sPop()`, it **does** overwrite the removed slot with `'-'`;
- it **doesn't return** the removed value — which is not much use in a real program. You will fix that in exercise E4.

> 📝 **Efficiency:** enqueue and dequeue are both **O(1)** — no items are ever shifted along the array.
""")

exercise("E3", "Peek at the front",
"""
Write `qPeek()` that **returns** the item at the front of the queue *without removing it*. If the queue is empty, print `"Queue is empty"` and return `None`.
""",
'''
def qPeek():
    # Your code here
    pass
''',
'''
qInit()
check("qPeek() on an empty queue", qPeek(), None)
qAdd(10); qAdd(20)
check("qPeek() returns the front", qPeek(), 10)
check("qPeek() does not remove", qCount, 2)
qRemove()
check("qPeek() after a remove", qPeek(), 20)
''',
'''
def qPeek():
    if qEmpty():
        print("Queue is empty")
        return None
    return qData[qFront]   # front item; no pointers change
''')

exercise("E4", "A dequeue that returns the value",
"""
Write `qDequeue()`: it does the same as `qRemove()` **but also returns the value it removed** (or `None` if the queue was empty).

*Hint:* save `qData[qFront]` in a variable **before** you overwrite it and move the pointer. Don't forget the `global` statement!
""",
'''
def qDequeue():
    # Your code here
    pass
''',
'''
qInit()
qAdd("A"); qAdd("B")
check("first dequeue", qDequeue(), "A")
check("second dequeue", qDequeue(), "B")
check("dequeue on empty queue", qDequeue(), None)

qInit()
for i in [1, 2, 3, 4]:
    qAdd(i)
qDequeue(); qDequeue()
qAdd(5); qAdd(6)   # these two wrap around to indexes 0 and 1
check("order after wrap-around", [qDequeue() for _ in range(4)], [3, 4, 5, 6])
''',
'''
def qDequeue():
    global qFront, qCount
    if qEmpty():
        print("Queue is empty")
        return None
    value = qData[qFront]              # save it before it is overwritten
    qData[qFront] = '-'
    qFront = (qFront + 1) % qSize      # move the front pointer circularly
    qCount = qCount - 1
    return value
''')

# ---------------------------------------------------------------- 4. Linked list
md("""
# 4. The Linked List

A **linked list** is an ordered sequence of **nodes**. Each node stores:
- a piece of **data**, and
- a **pointer** to the next node.

A **start pointer** tells us where the first node is; the last node's pointer is `-1` (null).

The big idea: the **logical order** of the list (following the pointers) does **not** have to match the **physical order** in memory. So we can insert or delete in the middle **by changing a couple of pointers**, without shifting any data.

| | Array | Linked list |
|---|---|---|
| Access the *i*-th item | direct — O(1) | must follow pointers — O(n) |
| Insert / delete in the middle | shift items — O(n) | change pointers (after finding the place) |
| Extra memory | none | one pointer per node |

### Implementation with two parallel arrays

| Variable | Role |
|---|---|
| `lData[i]` | the data stored in node `i` |
| `lLinks[i]` | the index of the node that comes **after** node `i` (`-1` = end) |
| `lStart` | index of the **first** node of the list (`-1` = empty list) |
| `lHeap` | index of the first **free** node — the start of the **free list** |

### The free list ("heap")

All nodes that are **not** in the list are chained together into a second linked list: the **free list**. At the start *every* node is free, so `lInit()` links them in order: `0 → 1 → 2 → … → 39 → -1`, with `lHeap = 0`.

- `lAllocateNode(value)` **takes** the first node off the free list (like a pop).
- `lReleaseNode(node)` **gives** a deleted node back to the front of the free list (like a push).

> 💡 The free list is itself a **stack of unused nodes**. Every node is always in exactly **one** of the two lists — the data list or the free list. "Heap" here just means "pool of free memory"; it has nothing to do with the heap data structure.

Here is `linked_list.py`, unchanged:
""")
code(src("linked_list.py"))
md("Two helpers: one to show the arrays, one to return the values in logical order (useful for testing):")
code('''
def lShow(n=6):
    """Show the first n nodes of the two arrays, plus both start pointers."""
    print("index | lData | lLinks")
    print("------+-------+-------")
    for i in range(n):
        print(f"{i:>5} | {str(lData[i]):>5} | {lLinks[i]:>6}")
    print(f"lStart = {lStart}, lHeap = {lHeap}")

def lToList():
    """Return the values in logical (linked) order as a Python list."""
    values = []
    current = lStart
    while current != -1:
        values.append(lData[current])
        current = lLinks[current]
    return values
''')
md("### The initial state: every node is free")
code('''
lInit()
lShow()
''')
md("""
### Inserting in ascending order

`lInsert(value, mode)` supports three modes: `0` = insert at the start, `1` = keep the list in **ascending** order, `2` = keep it in **descending** order. Let's insert 30, 10 and 20 in ascending order:
""")
code('''
lInit()
for value in [30, 10, 20]:
    lInsert(value, 1)
lShow()
print("Logical order:", lToList())
''')
fig(svg_linked, "Logical view: lStart → [1] 10 → [2] 20 → [0] 30. The free list starts at node 3.")
md("""
Physically the data is stored as `30, 10, 20` (in the order it arrived), but following the pointers from `lStart` gives `10 → 20 → 30`.

### How `lInsert` finds the right place — the *prev / current* pattern

`lInsert` walks along the list with **two** pointers:
- `current` — the node we are looking at,
- `prev` — the node just before it.

It stops when it finds the first node whose value is bigger than the new one (mode 1). The new node then goes **between `prev` and `current`**:

```
lLinks[newNode] = current     # 1) the new node points to current
lLinks[prev]    = newNode     # 2) prev now points to the new node
```

If `prev` is still `-1`, the new node goes at the very start, so `lStart` changes instead.

> ⚠️ **Exam tip:** the order of those two assignments matters. If you overwrite `lLinks[prev]` first, you lose the only reference to `current`!

### Deleting, and recycling the node
""")
code('''
lRemove(20)          # node 2 is unlinked and returned to the free list
lShow()
print("Logical order:", lToList())
print()
lInsert(25, 1)       # the new value reuses node 2
lShow()
print("Logical order:", lToList())
''')
fig(svg_linked, "After deleting 20 and inserting 25: node 2 was released to the free list and then allocated again.")
md("""
### The three insert modes and searching
""")
code('''
for mode in [0, 1, 2]:
    lInit()
    for value in [3, 1, 2]:
        lInsert(value, mode)
    print("mode", mode, "->", lToList())

print()
lSearch(3)
lSearch(99)
''')
md("""
> 📝 **Efficiency:** searching, ordered insertion and deletion are **O(n)** because we may have to follow every pointer. Inserting at the start *could* be **O(1)** — but look closely at `lInsert`: in mode 0 the `while` loop still walks the **whole** list before inserting at the start, because the stopping condition only applies to modes 1 and 2. The result is correct, just slower than necessary. 🤔 *How would you change `lInsert` so that mode 0 skips the loop?*

Note that `lSearch` **prints** its result instead of returning it. In a real program (and in the exam) a search function usually **returns** the index, or `-1` if the value isn't there — see exercise E7.
""")

exercise("E5", "Count the nodes",
"""
Write `lCount()` that returns how many nodes are in the list, by following the pointers from `lStart` until you reach `-1`.
""",
'''
def lCount():
    # Your code here
    pass
''',
'''
lInit()
check("empty list", lCount(), 0)
for v in [5, 3, 8, 1, 9]:
    lInsert(v, 1)
check("five nodes", lCount(), 5)
lRemove(8)
check("after one removal", lCount(), 4)
''',
'''
def lCount():
    count = 0
    current = lStart
    while current != -1:            # follow the pointers to the end
        count += 1
        current = lLinks[current]
    return count
''')

exercise("E6", "Reverse the list in place",
"""
Write `lReverse()` that reverses the list **by changing the pointers only** — no data moves and no new nodes are allocated.

*Hint:* walk along the list with three variables, `prev`, `current` and `nextNode`. For each node, save its next node, point it back to `prev`, then move all three along. At the end `lStart` must point to the old last node.
""",
'''
def lReverse():
    # Your code here
    pass
''',
'''
lInit()
for v in [1, 2, 3, 4]:
    lInsert(v, 1)
lReverse()
check("reverse 1-2-3-4", lToList(), [4, 3, 2, 1])
check("data did not move", lData[:4], [1, 2, 3, 4])

lInit()
lReverse()
check("reverse an empty list", lToList(), [])
''',
'''
def lReverse():
    global lStart
    prev = -1
    current = lStart
    while current != -1:
        nextNode = lLinks[current]   # remember where to go next
        lLinks[current] = prev       # turn this node's arrow around
        prev = current
        current = nextNode
    lStart = prev                    # the old last node is the new first node
''')

exercise("E7", "A search that returns",
"""
Write `lFind(value)` that **returns** the index of the node containing `value`, or `-1` if it is not in the list (or the list is empty). It must not print anything.
""",
'''
def lFind(value):
    # Your code here
    pass
''',
'''
lInit()
check("empty list", lFind(5), -1)
for v in [30, 10, 20]:
    lInsert(v, 1)
check("find 20", lFind(20), 2)
check("find 30", lFind(30), 0)
check("value not present", lFind(99), -1)
''',
'''
def lFind(value):
    current = lStart
    while current != -1:
        if lData[current] == value:
            return current
        current = lLinks[current]
    return -1
''')

# ---------------------------------------------------------------- 5. Binary tree
md("""
# 5. The Binary Search Tree

A **binary tree** is made of **nodes**; each node has data and **at most two children**, a *left* one and a *right* one. The top node is the **root**; nodes with no children are **leaves**.

A **binary search tree (BST)** adds an ordering rule:

> for every node, values in its **left** subtree are **smaller**, and values in its **right** subtree are **greater or equal**.

This rule means that at each node we can throw away half of the remaining tree — like a binary search.

**Where trees are used:** fast searching and sorting, database indexes, file-system hierarchies, expression trees, decision trees.

### Implementation with three parallel arrays

| Variable | Role |
|---|---|
| `bData[i]` | the data in node `i` |
| `bLeft[i]` | index of the **left** child of node `i` (`-1` = none) |
| `bRight[i]` | index of the **right** child of node `i` (`-1` = none) |
| `bRoot` | index of the root (`-1` = empty tree) |
| `bHeap` | index of the first **free** node |

> 💡 **Clever trick:** while a node is free, it doesn't need children, so the code **reuses `bLeft` as the "next free node" pointer**. That's why `bInit()` sets `bLeft[i] = i + 1`, and why `bAllocateNode` resets both child pointers to `-1` as soon as it hands a node out.

Here is `binary_tree.py`, unchanged:
""")
code(src("binary_tree.py"))
code('''
def bShow(n=8):
    """Show the first n nodes of the three arrays, plus the root and free pointers."""
    print("index | bData | bLeft | bRight")
    print("------+-------+-------+-------")
    for i in range(n):
        print(f"{i:>5} | {str(bData[i]):>5} | {bLeft[i]:>5} | {bRight[i]:>6}")
    print(f"bRoot = {bRoot}, bHeap = {bHeap}")
''')
md("### Building a tree")
code('''
bInit()
for value in [5, 7, 3, 1, 9, 0]:
    bInsert(value)
bShow()
''')
fig(svg_tree, "The tree built by inserting 5, 7, 3, 1, 9, 0. The small grey numbers are the array indexes of the nodes.")
md("""
Read the table together with the picture: node `[0]` holds 5, its left child is node `2` (value 3) and its right child is node `1` (value 7). Nodes 6 and 7 are still free — their `bLeft` values form the free list `6 → 7 → 8 → …`.

### How insertion and search work

Both start at the root and repeat: *if the value is smaller go **left**, otherwise go **right*** — until they reach a `-1`.
- **search** stops early if it finds the value;
- **insert** remembers the last real node (`parent`) and hangs the new node on its left or right.
""")
code('''
bSearch(1)     # path: 5 -> 3 -> 1
bSearch(9)     # path: 5 -> 7 -> 9
bSearch(-1)    # path: 5 -> 3 -> 1 -> 0 -> (no left child) -> not found
''')
md("""
### Traversals

A **traversal** visits every node once. For binary trees there are three classic recursive orders:

| Traversal | Order | Use |
|---|---|---|
| **Pre-order** | node → left → right | copying a tree, prefix (Polish) notation |
| **In-order** | left → node → right | outputs a BST in **sorted order** |
| **Post-order** | left → right → node | deleting a tree, postfix (Reverse Polish) notation |

Here is pre-order as a worked example. Notice the **base case** (`node == -1`, an empty subtree) and the two **recursive calls**:
""")
code('''
def bPreOrder(node):
    """Visit the node, then its left subtree, then its right subtree."""
    if node != -1:
        print(bData[node], end=" ")
        bPreOrder(bLeft[node])
        bPreOrder(bRight[node])

bPreOrder(bRoot)
''')
md("""
### When a BST goes wrong

Searching a BST is **O(log n)** when the tree is **balanced**. But the shape depends on the **order of insertion**. Watch what happens if the data arrives already sorted:
""")
code('''
bInit()
for value in [1, 2, 3, 4, 5]:
    bInsert(value)
bShow(6)
''')
fig(svg_tree, "Inserting sorted data gives a degenerate tree: every node only has a right child.")
md("""
The tree has become a **linked list** in disguise, and searching is back to **O(n)**. (Self-balancing trees such as AVL trees fix this — beyond the A Level spec, but worth knowing.)

> 📝 Insert and search in a BST are **O(log n)** on average and **O(n)** in the worst case.
""")

exercise("E8", "Smallest and largest values",
"""
Write `bMin()` and `bMax()` that **return** the smallest and largest value in the tree, or `None` if the tree is empty.

*Hint:* where is the smallest value in a BST? Keep going left from the root until there is no left child.

> 🤔 **Careful with names:** the node you reach is the **leftmost node**, which is *not always a leaf*. Insert 10, 5, 7: the minimum is 5, but node 5 still has a right child (7)!
""",
'''
def bMin():
    # Your code here
    pass

def bMax():
    # Your code here
    pass
''',
'''
bInit()
check("bMin() on an empty tree", bMin(), None)
for v in [50, 30, 70, 20, 40, 60, 80]:
    bInsert(v)
check("bMin()", bMin(), 20)
check("bMax()", bMax(), 80)

bInit()
for v in [10, 5, 7]:
    bInsert(v)
check("minimum that is not a leaf", bMin(), 5)
''',
'''
def bMin():
    if bEmpty():
        return None
    current = bRoot
    while bLeft[current] != -1:      # keep going left
        current = bLeft[current]
    return bData[current]

def bMax():
    if bEmpty():
        return None
    current = bRoot
    while bRight[current] != -1:     # keep going right
        current = bRight[current]
    return bData[current]
''')

exercise("E9", "In-order and post-order traversals",
"""
Using `bPreOrder` as a model, write two **recursive** functions that **return a Python list** of the values (instead of printing them):

- `bInOrder(node)` — left, node, right
- `bPostOrder(node)` — left, right, node

Call them with `bRoot`. For a BST, the in-order list should come out **sorted**.
""",
'''
def bInOrder(node):
    # Your code here
    pass

def bPostOrder(node):
    # Your code here
    pass
''',
'''
bInit()
for v in [5, 7, 3, 1, 9, 0]:
    bInsert(v)
check("in-order is sorted", bInOrder(bRoot), [0, 1, 3, 5, 7, 9])
check("post-order", bPostOrder(bRoot), [0, 1, 3, 9, 7, 5])
bInit()
check("empty tree", bInOrder(bRoot), [])
''',
'''
def bInOrder(node):
    if node == -1:                   # base case: empty subtree
        return []
    return bInOrder(bLeft[node]) + [bData[node]] + bInOrder(bRight[node])

def bPostOrder(node):
    if node == -1:
        return []
    return bPostOrder(bLeft[node]) + bPostOrder(bRight[node]) + [bData[node]]
''')

exercise("E10", "⭐ Challenge: height of the tree",
"""
The **height** of a tree is the number of nodes on the longest path from the root down to a leaf (an empty tree has height 0). Write a recursive `bHeight(node)`.

*Hint:* the height of a node is 1 + the larger of the heights of its two subtrees.
""",
'''
def bHeight(node):
    # Your code here
    pass
''',
'''
bInit()
check("empty tree", bHeight(bRoot), 0)
for v in [5, 7, 3, 1, 9, 0]:
    bInsert(v)
check("tree 5,7,3,1,9,0", bHeight(bRoot), 4)
bInit()
for v in [1, 2, 3, 4, 5]:
    bInsert(v)
check("degenerate tree", bHeight(bRoot), 5)
''',
'''
def bHeight(node):
    if node == -1:
        return 0
    return 1 + max(bHeight(bLeft[node]), bHeight(bRight[node]))
''')

# ---------------------------------------------------------------- 6. Exam practice
md("""
# 6. Exam-style tracing questions

In the exam you won't have a computer: you will be asked to **trace** the arrays and pointers by hand. Do these **on paper first**, then check your answers.
""")

trace("T1", "Stack",
"""
`sInit()` is called, followed by:

`sPush("A")`, `sPush("B")`, `sPush("C")`, `sPop()`, `sPush("D")`, `sPop()`, `sPop()`

**(a)** Which values are returned by the three pops, in order?
**(b)** What is the final value of `sTop`?
**(c)** What do `sData[0]` to `sData[3]` contain at the end?
""",
"""
**(a)** `C`, `D`, `B` **(b)** `sTop = 0` **(c)** `A B D -`

`D` was pushed into index 2, **overwriting** `C`. After the last two pops, `B` and `D` are still physically in the array but are above `sTop`.
""",
'''
sInit()
sPush("A"); sPush("B"); sPush("C")
print(sPop())
sPush("D")
print(sPop())
print(sPop())
sShow(4)
''')

trace("T2", "Circular queue",
"""
`qInit()` is called (so `qSize = 4`), followed by:

`qAdd("A")`, `qAdd("B")`, `qAdd("C")`, `qRemove()`, `qRemove()`, `qAdd("D")`, `qAdd("E")`, `qAdd("F")`

**(a)** Give the final values of `qFront`, `qRear` and `qCount`.
**(b)** Give the contents of `qData[0]` to `qData[3]`.
**(c)** What happens if `qAdd("G")` is now called?
""",
"""
**(a)** `qFront = 2`, `qRear = 1`, `qCount = 4` **(b)** `E F C D` (queue order: `C D E F`) **(c)** the queue is full, so `Queue is full` is printed and nothing changes.
""",
'''
qInit()
qAdd("A"); qAdd("B"); qAdd("C")
qRemove(); qRemove()
qAdd("D"); qAdd("E"); qAdd("F")
qShow()
qAdd("G")
''')

trace("T3", "Linked list",
"""
`lInit()` is called, followed by:

`lInsert(40, 1)`, `lInsert(20, 1)`, `lInsert(30, 1)`, `lRemove(20)`, `lInsert(10, 1)`

Copy and complete the table for indexes 0–4, and give the final values of `lStart` and `lHeap`.

| index | lData | lLinks |
|---|---|---|
| 0 | | |
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
""",
"""
| index | lData | lLinks |
|---|---|---|
| 0 | 40 | -1 |
| 1 | 10 | 2 |
| 2 | 30 | 0 |
| 3 | - | 4 |
| 4 | - | 5 |

`lStart = 1`, `lHeap = 3`. Logical order: `10 → 30 → 40`. Node 1 was freed when 20 was removed and then **reused** for 10.
""",
'''
lInit()
lInsert(40, 1); lInsert(20, 1); lInsert(30, 1)
lRemove(20)
lInsert(10, 1)
lShow(5)
print("Logical order:", lToList())
''')

trace("T4", "Binary search tree",
"""
`bInit()` is called, then these values are inserted in this order:

`50, 30, 70, 20, 40, 60, 80, 35`

**(a)** Draw the tree.
**(b)** Complete `bData`, `bLeft` and `bRight` for indexes 0–9, and give `bRoot` and `bHeap`.
**(c)** List the nodes visited when searching for 35.
**(d)** Give the in-order and pre-order traversals.
""",
"""
**(b)** see the table below. `bRoot = 0`, `bHeap = 8`; nodes 8 and 9 are free (`bLeft[8] = 9`, `bLeft[9] = -1`).
**(c)** 50 → 30 → 40 → 35
**(d)** in-order: `20 30 35 40 50 60 70 80`; pre-order: `50 30 20 40 35 70 60 80`
""",
'''
bInit()
for v in [50, 30, 70, 20, 40, 60, 80, 35]:
    bInsert(v)
bShow(10)
print("In-order: ", bInOrder(bRoot))
print("Pre-order: ", end="")
bPreOrder(bRoot)
''')

# ---------------------------------------------------------------- 7. Summary
md("""
# 7. Summary

| ADT | Order | Pointers | Add | Remove | Search |
|---|---|---|---|---|---|
| **Stack** | LIFO | `sTop` | O(1) push | O(1) pop | — |
| **Circular queue** | FIFO | `qFront`, `qRear` (+ `qCount`) | O(1) at rear | O(1) at front | — |
| **Linked list** | by links (e.g. sorted) | `lStart`, `lHeap`, `lLinks[]` | O(n) sorted, O(1) at start | O(n) | O(n) linear |
| **Binary search tree** | left < node ≤ right | `bRoot`, `bHeap`, `bLeft[]`, `bRight[]` | O(log n) avg | — | O(log n) avg, O(n) worst |

### Checklist before the exam

- [ ] I can explain the difference between an ADT and its implementation.
- [ ] I know what `-1` means for every pointer, and the initial value of every pointer.
- [ ] I can trace a stack and show that popping doesn't erase data.
- [ ] I can use `% qSize` to wrap a circular queue, and explain why `qCount` is useful.
- [ ] I can explain the free list: how nodes are allocated and released.
- [ ] I can insert into and delete from a linked list with the *prev / current* pattern.
- [ ] I can draw a BST from an insertion order **and** fill in its `bLeft`/`bRight` arrays.
- [ ] I can write pre-, in- and post-order traversals recursively.

### Common mistakes

1. Forgetting `global` when a function changes `sTop`, `qFront`, `lStart`…
2. Not checking `Empty()` / `Full()` before removing / adding (underflow / overflow).
3. Reading a circular queue from index 0 instead of from `qFront`.
4. Updating linked-list pointers in the wrong order and losing part of the list.
5. Forgetting the special case where the **first** node changes (`prev == -1`).
6. Thinking that a deleted node disappears — in fact it goes back to the **free list**.
""")


# --------------------------------------------------------------------------
# Execute everything in order (to get real outputs and diagrams)
# --------------------------------------------------------------------------
NS = {}
FAILURES = []


def run(text):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(text, "<tutorial>", "exec"), NS)
    out = buf.getvalue()
    if "❌" in out:
        FAILURES.append(out)
    return out


for c in CELLS:
    if c["kind"] == "code" and c["run"]:
        c["out"] = run(c["text"])
    elif c["kind"] == "fig":
        c["svg"] = c["fn"](NS)
    elif c["kind"] == "ex":
        c["sol_out"] = run(c["solution"])
        c["test_out"] = run(c["tests"])
    elif c["kind"] == "trace":
        c["out"] = run(c["answer_code"])
        if c["id"] == "T4":
            c["svg"] = svg_tree(NS)

if FAILURES:
    print("TEST FAILURES:\n" + "\n".join(FAILURES))
    sys.exit(1)


# --------------------------------------------------------------------------
# Notebook
# --------------------------------------------------------------------------
def nb_md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def nb_code(text, hidden_title=None):
    if hidden_title:
        text = f'#@title {hidden_title} {{ display-mode: "form" }}\n' + text
    meta = {"cellView": "form"} if hidden_title else {}
    return {"cell_type": "code", "metadata": meta, "execution_count": None, "outputs": [],
            "source": text.splitlines(keepends=True)}


def svg_md(svg, caption):
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"![diagram](data:image/svg+xml;base64,{b64})\n\n*{caption}*"


nb_cells = []
for c in CELLS:
    k = c["kind"]
    if k == "md":
        nb_cells.append(nb_md(c["text"]))
    elif k == "code":
        nb_cells.append(nb_code(c["text"]))
    elif k == "fig":
        nb_cells.append(nb_md(svg_md(c["svg"], c["caption"])))
    elif k == "ex":
        nb_cells.append(nb_md(f"### ✏️ Exercise {c['id']} — {c['title']}\n\n{c['task']}"))
        nb_cells.append(nb_code(c["skeleton"]))
        nb_cells.append(nb_md(f"🧪 **Test your answer to {c['id']}:**"))
        nb_cells.append(nb_code(c["tests"]))
        nb_cells.append(nb_code(c["solution"], hidden_title=f"✅ Solution {c['id']} — double-click to reveal"))
    elif k == "trace":
        nb_cells.append(nb_md(f"### 🖊️ {c['id']} — {c['title']}\n\n{c['question']}"))
        nb_cells.append(nb_code(c["answer_code"], hidden_title=f"✅ Run to check your answer to {c['id']}"))
        nb_cells.append(nb_md(f"<details><summary><b>Show the explained answer to {c['id']}</b></summary>\n\n"
                              f"{c['answer_md']}\n\n</details>"))

notebook = {
    "nbformat": 4, "nbformat_minor": 0,
    "metadata": {"colab": {"provenance": [], "toc_visible": True},
                 "kernelspec": {"name": "python3", "display_name": "Python 3"},
                 "language_info": {"name": "python"}},
    "cells": nb_cells,
}
nb_path = os.path.join(OUT, "ADTs_Y13_Tutorial.ipynb")
with open(nb_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, ensure_ascii=False, indent=1)


# --------------------------------------------------------------------------
# HTML -> PDF
# --------------------------------------------------------------------------
FMT = HtmlFormatter(nowrap=True, style="friendly")


def h_md(text):
    return markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])


def h_code(text, label=None, cls="code"):
    lab = f"<div class='label'>{label}</div>" if label else ""
    return f"<div class='block {cls}'>{lab}<pre>{highlight(text, PythonLexer(), FMT)}</pre></div>"


def h_out(text):
    if not text.strip():
        return ""
    return f"<div class='block out'><div class='label'>Output</div><pre>{html.escape(text.rstrip())}</pre></div>"


def h_fig(svg, caption):
    return f"<figure>{svg}<figcaption>{html.escape(caption)}</figcaption></figure>"


body, appendix_ex, appendix_tr, toc = [], [], [], []
first = True
for c in CELLS:
    k = c["kind"]
    if k == "md":
        text = c["text"]
        if first:  # title cell -> cover page
            first = False
            body.append("<section class='cover'>" + h_md(text) + "<div id='toc'></div></section>")
            continue
        if text.startswith("# "):
            toc.append(text.splitlines()[0][2:])
        body.append(h_md(text))
    elif k == "code":
        if "def check(" in c["text"]:
            continue  # notebook-only helper
        body.append(h_code(c["text"]) + h_out(c.get("out", "")))
    elif k == "fig":
        body.append(h_fig(c["svg"], c["caption"]))
    elif k == "ex":
        body.append(f"<div class='exercise'><h3>✏️ Exercise {c['id']} — {html.escape(c['title'])}</h3>"
                    + h_md(c["task"]) + h_code(c["skeleton"], "Starter code")
                    + h_code(c["tests"], "Tests (run these in the notebook)", "tests") + "</div>")
        appendix_ex.append(f"<div class='sol'><h3>{c['id']} — {html.escape(c['title'])}</h3>"
                           + h_code(c["solution"]) + h_out(c["sol_out"] + c["test_out"]) + "</div>")
    elif k == "trace":
        body.append(f"<div class='exercise trace'><h3>🖊️ {c['id']} — {html.escape(c['title'])}</h3>"
                    + h_md(c["question"]) + "</div>")
        extra = h_fig(c["svg"], "The tree for T4.") if "svg" in c else ""
        appendix_tr.append(f"<div class='sol'><h3>{c['id']} — {html.escape(c['title'])}</h3>"
                           + h_md(c["answer_md"]) + extra + h_code(c["answer_code"], "Check") + h_out(c["out"]) + "</div>")

toc.append("Appendix A. Solutions to the exercises")
toc.append("Appendix B. Answers to the tracing questions")
toc_html = "<h2>Contents</h2><ol class='toc'>" + "".join(f"<li>{html.escape(t)}</li>" for t in toc) + "</ol>"
body = [b.replace("<div id='toc'></div>", toc_html) for b in body]
body.append("<h1>Appendix A. Solutions to the exercises</h1>"
            "<p>Each solution is followed by the output of the test cells, all passing.</p>" + "".join(appendix_ex))
body.append("<h1>Appendix B. Answers to the tracing questions</h1>" + "".join(appendix_tr))

CSS = """
@page { size: A4; margin: 18mm 17mm 18mm 17mm;
  @bottom-center { content: counter(page); font: 9pt 'Segoe UI', sans-serif; color: #64748b; } }
@page :first { @bottom-center { content: none; } }
body { font-family: 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 10.5pt; line-height: 1.5; color: #0f172a; background: white; }
h1 { break-before: page; font-size: 21pt; color: #1e3a8a; border-bottom: 3px solid #2563eb; padding-bottom: 4px; margin: 0 0 12px; }
h2 { font-size: 14pt; color: #1e3a8a; margin: 18px 0 6px; }
h3 { font-size: 12pt; color: #1e40af; margin: 16px 0 6px; break-after: avoid; }
p, li { orphans: 3; widows: 3; }
code { font-family: Consolas, Menlo, monospace; font-size: 9.5pt; background: #eef2ff; padding: 0 3px; border-radius: 3px; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; margin: 8px 0 12px; font-size: 9.8pt; break-inside: avoid; }
th, td { border: 1px solid #cbd5e1; padding: 4px 8px; text-align: left; vertical-align: top; }
th { background: #e0e7ff; }
blockquote { margin: 10px 0; padding: 8px 12px; background: #f0f9ff; border-left: 4px solid #0ea5e9; border-radius: 4px; break-inside: avoid; }
blockquote p { margin: 0; }
.block { margin: 8px 0; border-radius: 6px; break-inside: avoid; }
.block pre { margin: 0; padding: 8px 10px; font-family: Consolas, Menlo, monospace; font-size: 8.8pt; line-height: 1.38; white-space: pre-wrap; }
.block.code { background: #f8fafc; border: 1px solid #cbd5e1; }
.block.tests { background: #fafaf9; border: 1px dashed #a8a29e; }
.block.out { background: #0f172a; color: #e2e8f0; border: 1px solid #0f172a; }
.block.out .label { color: #94a3b8; }
.label { font-size: 8pt; text-transform: uppercase; letter-spacing: .06em; color: #64748b; padding: 5px 10px 0; }
pre:not(.block pre) { background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px 10px; font-size: 9pt; }
figure { margin: 12px 0; text-align: center; break-inside: avoid; }
figure svg { max-width: 100%; height: auto; }
figcaption { font-size: 9pt; color: #475569; font-style: italic; margin-top: 4px; }
.exercise { border: 2px solid #f59e0b; background: #fffbeb; border-radius: 8px; padding: 2px 14px 8px; margin: 14px 0; }
.exercise.trace { border-color: #8b5cf6; background: #f5f3ff; }
.exercise h3 { color: #92400e; }
.exercise.trace h3 { color: #5b21b6; }
.sol { break-inside: auto; margin-bottom: 14px; }
.cover { text-align: left; padding-top: 30mm; }
.cover h1 { break-before: auto; font-size: 30pt; border: none; }
.cover h3 { font-size: 15pt; color: #475569; font-weight: normal; margin-top: 0; }
.toc { list-style: none; padding-left: 0; }
.toc li { margin: 3px 0; font-size: 11.5pt; }
""" + FMT.get_style_defs(".block.code pre, .block.tests pre")

doc = (f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>ADTs in Python — Y13</title>"
       f"<style>{CSS}</style></head><body>{''.join(body)}</body></html>")
html_path = os.path.join(WORK, "ADTs_Y13_Tutorial.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(doc)

pdf_path = os.path.join(OUT, "ADTs_Y13_Tutorial.pdf")
chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                f"--user-data-dir={os.path.join(WORK, 'chrome-profile')}",
                f"--print-to-pdf={pdf_path}", "file:///" + html_path.replace("\\", "/")],
               check=True, capture_output=True, timeout=120)
print("Notebook:", nb_path)
print("PDF:     ", pdf_path)
print("HTML:    ", html_path)
