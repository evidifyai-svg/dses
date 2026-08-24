#!/usr/bin/env python3
"""Write the machine-generated claim counts into CLAIMS-CLASSIFICATION and Annex D.

The inventory of normative claims is derived from the rows, never typed. A
hand-maintained count drifted three ways in the previous release candidate,
which is precisely the failure mode this specification exists to prevent
elsewhere.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "release_lint.py"), "--emit-counts"],
                     capture_output=True, text=True).stdout.strip().splitlines()
cls_line, sup_line = out[0], out[1]

p = os.path.join(ROOT, "CLAIMS-CLASSIFICATION.md")
c = open(p).read()
c = re.sub(r"Verification class: .*?\n", cls_line + "\n", c, count=1)
c = re.sub(r"Reference verifier support: \*\*implemented\*\*.*?\n", sup_line + "\n", c, count=1)
open(p, "w").write(c)

m_cls = dict(re.findall(r"\*\*([SCXTA])\*\* (\d+)", cls_line))
m_sup = dict(re.findall(r"\*\*(implemented|partial|not_implemented)\*\* (\d+)", sup_line))
want = (f"Current counts: {m_cls['S']} S, {m_cls['C']} C, {m_cls['X']} X, {m_cls['T']} T, "
        f"{m_cls['A']} A; {m_sup['implemented']} implemented, {m_sup['partial']} partial, "
        f"{m_sup['not_implemented']} not implemented.")
p = os.path.join(ROOT, "DSES-v0.2.md")
s = open(p).read()
s = re.sub(r"Current counts:[^\n]*", want, s, count=1)
open(p, "w").write(s)
print(cls_line)
print(sup_line)
