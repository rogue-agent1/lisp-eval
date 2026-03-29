#!/usr/bin/env python3
"""lisp_eval - Minimal Lisp evaluator with lambda, define, and let."""
import sys

def tokenize(s):
    return s.replace("(", " ( ").replace(")", " ) ").split()

def parse(tokens):
    if not tokens:
        raise SyntaxError("Unexpected EOF")
    token = tokens.pop(0)
    if token == "(":
        lst = []
        while tokens[0] != ")":
            lst.append(parse(tokens))
        tokens.pop(0)
        return lst
    elif token == ")":
        raise SyntaxError("Unexpected )")
    else:
        try: return int(token)
        except ValueError:
            try: return float(token)
            except ValueError: return token

class Env(dict):
    def __init__(self, params=(), args=(), outer=None):
        self.update(zip(params, args))
        self.outer = outer
    def find(self, key):
        if key in self: return self
        if self.outer: return self.outer.find(key)
        raise NameError(f"Undefined: {key}")

def standard_env():
    env = Env()
    env.update({
        "+": lambda *a: sum(a), "-": lambda a, b: a - b,
        "*": lambda a, b: a * b, "/": lambda a, b: a // b,
        "=": lambda a, b: a == b, "<": lambda a, b: a < b,
        ">": lambda a, b: a > b, ">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b, "not": lambda a: not a,
        "car": lambda x: x[0], "cdr": lambda x: x[1:],
        "cons": lambda a, b: [a] + list(b), "list": lambda *a: list(a),
        "null?": lambda x: x == [], "length": lambda x: len(x),
        "abs": abs, "min": min, "max": max, "mod": lambda a,b: a%b,
        "#t": True, "#f": False,
    })
    return env

def eval_expr(x, env):
    if isinstance(x, str):
        return env.find(x)[x]
    if not isinstance(x, list):
        return x
    if x[0] == "quote":
        return x[1]
    if x[0] == "if":
        _, test, conseq, alt = x
        return eval_expr(conseq if eval_expr(test, env) else alt, env)
    if x[0] == "define":
        _, var, expr = x
        env[var] = eval_expr(expr, env)
        return None
    if x[0] == "lambda":
        _, params, body = x
        return lambda *args: eval_expr(body, Env(params, args, env))
    if x[0] == "let":
        _, bindings, body = x
        new_env = Env(outer=env)
        for name, expr in bindings:
            new_env[name] = eval_expr(expr, env)
        return eval_expr(body, new_env)
    if x[0] == "begin":
        result = None
        for expr in x[1:]:
            result = eval_expr(expr, env)
        return result
    proc = eval_expr(x[0], env)
    args = [eval_expr(a, env) for a in x[1:]]
    return proc(*args)

def run(code):
    tokens = tokenize(code)
    results = []
    while tokens:
        expr = parse(tokens)
        r = eval_expr(expr, standard_env())
        if r is not None:
            results.append(r)
    return results

def test():
    assert run("(+ 1 2)") == [3]
    assert run("(* 3 4)") == [12]
    assert run("(if (> 3 2) 1 0)") == [1]
    assert run("(if (< 3 2) 1 0)") == [0]
    env = standard_env()
    tokens = tokenize("(define x 10)")
    eval_expr(parse(tokens), env)
    assert env["x"] == 10
    tokens2 = tokenize("(+ x 5)")
    assert eval_expr(parse(tokens2), env) == 15
    assert run("((lambda (x) (* x x)) 5)") == [25]
    assert run("(let ((a 3) (b 4)) (+ a b))") == [7]
    assert run("(abs (- 3 10))") == [7]
    assert run("(quote (1 2 3))") == [[1, 2, 3]]
    print("All tests passed!")

if __name__ == "__main__":
    test() if "--test" in sys.argv else print("lisp_eval: Lisp evaluator. Use --test")
