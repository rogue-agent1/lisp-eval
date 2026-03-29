#!/usr/bin/env python3
"""lisp_eval: Minimal Lisp/Scheme interpreter."""
import sys, re

def tokenize(s):
    return s.replace("(", " ( ").replace(")", " ) ").split()

def parse(tokens):
    if not tokens: raise SyntaxError("Unexpected EOF")
    t = tokens.pop(0)
    if t == "(":
        L = []
        while tokens[0] != ")":
            L.append(parse(tokens))
        tokens.pop(0)
        return L
    elif t == ")":
        raise SyntaxError("Unexpected )")
    else:
        try: return int(t)
        except ValueError:
            try: return float(t)
            except ValueError: return t

class Env(dict):
    def __init__(self, params=(), args=(), outer=None):
        self.update(zip(params, args))
        self.outer = outer
    def find(self, var):
        if var in self: return self
        if self.outer: return self.outer.find(var)
        raise NameError(f"Undefined: {var}")

def standard_env():
    env = Env()
    import math, operator as op
    env.update({
        "+": lambda *a: sum(a), "-": lambda a, b=None: -a if b is None else a-b,
        "*": lambda *a: eval("*".join(str(x) for x in a)) if len(a)>2 else a[0]*a[1] if len(a)==2 else a[0],
        "/": lambda a, b: a / b, "//": lambda a, b: a // b,
        ">": op.gt, "<": op.lt, ">=": op.ge, "<=": op.le, "=": op.eq,
        "abs": abs, "max": max, "min": min, "not": lambda x: not x,
        "car": lambda x: x[0], "cdr": lambda x: x[1:],
        "cons": lambda a, b: [a] + b, "list": lambda *a: list(a),
        "length": len, "null?": lambda x: x == [],
        "number?": lambda x: isinstance(x, (int, float)),
        "print": lambda x: print(x),
        "#t": True, "#f": False, "nil": [],
    })
    # Fix multiply
    env["*"] = lambda *a: eval("1" if not a else "*".join(str(x) for x in a))
    return env

def evaluate(x, env):
    if isinstance(x, str):
        return env.find(x)[x]
    elif not isinstance(x, list):
        return x
    elif x[0] == "quote":
        return x[1]
    elif x[0] == "if":
        _, test, conseq = x[0:3]
        alt = x[3] if len(x) > 3 else None
        return evaluate(conseq if evaluate(test, env) else alt, env)
    elif x[0] == "define":
        _, var, expr = x
        env[var] = evaluate(expr, env)
    elif x[0] == "lambda":
        _, params, body = x
        return lambda *args: evaluate(body, Env(params, args, env))
    elif x[0] == "begin":
        val = None
        for expr in x[1:]:
            val = evaluate(expr, env)
        return val
    elif x[0] == "let":
        _, bindings, body = x
        params = [b[0] for b in bindings]
        args = [evaluate(b[1], env) for b in bindings]
        return evaluate(body, Env(params, args, env))
    else:
        proc = evaluate(x[0], env)
        args = [evaluate(a, env) for a in x[1:]]
        return proc(*args)

def run(code):
    tokens = tokenize(code)
    results = []
    while tokens:
        expr = parse(tokens)
        r = evaluate(expr, standard_env())
        if r is not None:
            results.append(r)
    return results

def test():
    env = standard_env()
    # Basic arithmetic
    assert evaluate(parse(tokenize("(+ 1 2)")), env) == 3
    assert evaluate(parse(tokenize("(- 10 3)")), env) == 7
    # Define and use
    evaluate(parse(tokenize("(define x 42)")), env)
    assert evaluate(parse(tokenize("x")), env) == 42
    # Lambda
    evaluate(parse(tokenize("(define square (lambda (x) (* x x)))")), env)
    assert evaluate(parse(tokenize("(square 5)")), env) == 25
    # If
    assert evaluate(parse(tokenize("(if (> 3 2) 1 0)")), env) == 1
    assert evaluate(parse(tokenize("(if (< 3 2) 1 0)")), env) == 0
    # Recursion
    evaluate(parse(tokenize("(define fact (lambda (n) (if (<= n 1) 1 (* n (fact (- n 1))))))")), env)
    assert evaluate(parse(tokenize("(fact 5)")), env) == 120
    # List ops
    assert evaluate(parse(tokenize("(car (list 1 2 3))")), env) == 1
    assert evaluate(parse(tokenize("(cdr (list 1 2 3))")), env) == [2, 3]
    print("All tests passed!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test": test()
    else: print("Usage: lisp_eval.py test")
