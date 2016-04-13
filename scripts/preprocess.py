#!/usr/bin/env python

__def__ = """
Usage:
  preprocess compile <in> [<out>] [flags]
  preprocess compile_all <directory> [flags]
  preprocess reachability_all <directory> <output_file> [flags]
"""

import sys
import subprocess
import os
import csv

CLANG = os.environ.get("CLANG")
if not CLANG:
    CLANG = "clang"

STAT_CASES = ["SMT calls Subseteq()", "SMT calls Empty()", "SMT queries", "SMT queries SAT",
        "SMT queries unSAT", "SMT queries unSAT", "SMT subseteq on syntax. equal", 
        "SMT simplify calls", "SMT CACHED", "Instruction executed", "Instructions executed observable"]

def change_suffix(src, suffix, pre_suffix = ""):
    out, _ = os.path.splitext(src)
    out += pre_suffix + "." + suffix
    return out
  
## Taken from http://howto.pui.ch/post/37471155682/set-timeout-for-a-shell-command-in-python
def timeout_command(command, timeout):
    """call shell-command and either return its output or kill it
    if it doesn't normally exit within timeout seconds and return None"""
    import subprocess, datetime, os, time, signal
    start = datetime.datetime.now()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while process.poll() is None:
      time.sleep(0.1)
      now = datetime.datetime.now()
      if (now - start).seconds + (now - start).microseconds * 0.000001 > timeout:
        os.kill(process.pid, signal.SIGKILL)
        os.waitpid(-1, os.WNOHANG)
        return None, None
    return process.stdout.read() + process.stderr.read(), (now - start).seconds + (now - start).microseconds * 0.000001
    
def reachability(file, flags, timeout=120):
    print("Running reachability on file {0}".format(file))
    command = ["../bin/symdivine", "reachability", file, "-s"] + flags
    out, time = timeout_command(command, timeout)
        
    result = [str(time)] + (2 + 4 + len(STAT_CASES))*[None]
    
    if not out and not time:
        print("TIMEOUT")
        result[-1] = "TIMEOUT"
        return result
    
    lines = out.split("\n")
    
    try:
        if "Safe" in out:
            result[1] = "true"
        else:
            result[1] = "false"
            
        idx = lines.index("States count")
        result[2] = lines[idx + 2]
        
        idx = lines.index("General statistics") + 2
        while len(lines[idx]):
            s = lines[idx].split(":")
            s[0] = s[0].strip()
            i = STAT_CASES.index(s[0])
            result[3 + i] = s[1].strip()
            idx = idx + 1
            
        idx = lines.index("Query cache statistics")
        for i in range(3):
            result[3 + len(STAT_CASES) + i] = lines[idx + 2 + i].split(":")[1].strip()
    except ValueError:
        print("Warning! Unexpected output")
        print(out)
        result[-1] = "Unexpected output!\\n" + out.replace("\n", "\\n")
    
    return result
    
def reachability_all(dir, output_filename, flags):
    out_file = open(output_filename, "w")
    csv_file = csv.writer(out_file)
    csv_file.writerow(["name", "opt", "time", "result", "states"] + STAT_CASES + ["Hit count", "Miss count", "Replace count", "Note"])
    for file in os.listdir(dir):
        if file.endswith(".ll"):
            opt = "unknown"
            if file.endswith("o2.ll"):
                opt = "2"
            elif file.endswith("o1.ll"):
                opt = "1"
            elif file.endswith("o0.ll"):
                opt = "0"
            elif file.endswith("os.ll"):
                opt = "S"
            src = os.path.join(dir, file)
            r = reachability(src, flags)
            if not r:
                r = []
            csv_file.writerow([file, opt] + r)
            out_file.flush()
            os.fsync(out_file.fileno())
    
def compile(src, args, output = None):
    if not output:
        output = change_suffix(src, "ll")
        
    compiler = CLANG if src.endswith(".c") else CLANG + "++"
    cmd = compiler + " -S -m32 -emit-llvm {0} -o {1} {2}".format(' '.join(args), output, src)
    return os.system(cmd)
    
def compile_all(dir, args):
    for file in os.listdir(dir):
        if file.endswith(".c") or file.endswith(".cpp"):
            src = os.path.join(dir, file)
            if compile(src, args + ["-O0"], change_suffix(src, "ll", "_o0")) != 0:
                return 1
            if compile(src, args + ["-O2"], change_suffix(src, "ll", "_o2")) != 0:
                return 1
            if compile(src, args + ["-Os"], change_suffix(src, "ll", "_os")) != 0:
                return 1
    return 0   

if __name__ == "__main__":
    if len(sys.argv) == 1 or (not sys.argv[1] in ["compile", "compile_all", "reachability_all"]):
        print(__def__)
        sys.exit(1)
        
    if sys.argv[1] == "compile" and len(sys.argv) > 2:
        src = sys.argv[2]
        if len(sys.argv) > 3 and sys.argv[3][0] != "-":
            out = sys.argv[3]
            args = sys.argv[4:]
        else:
            out = None
            args = sys.argv[3:]
        if compile(src, args, out) != 0:
            print("ERROR")
            print("Compilation failed!")
            sys.exit(1)
        sys.exit(0)
    if sys.argv[1] == "compile_all" and len(sys.argv) > 2:
        if compile_all(sys.argv[2], sys.argv[3:]) != 0:
            print("ERROR")
            print("Compilation failed!")
            sys.exit(1)
        sys.exit(0)
        
    if sys.argv[1] == "reachability_all" and len(sys.argv) > 3:
        reachability_all(sys.argv[2], sys.argv[3], sys.argv[4:])
        sys.exit(0)
        
    print(__def__)
    sys.exit(1)