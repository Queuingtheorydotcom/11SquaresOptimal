"""Run one proof job at low priority with a bounded single-core duty cycle.

Only the subprocess group created here is signaled. Verification work is
serial; no discovery deadline should be inferred from its longer wall time.
"""
import argparse
import os
import signal
import subprocess
import time

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--percent',type=float,default=25)
    p.add_argument('command',nargs=argparse.REMAINDER)
    a=p.parse_args()
    if a.command and a.command[0]=='--':a.command=a.command[1:]
    if not 1<=a.percent<=100 or not a.command:p.error('Provide percent in [1,100] and a command.')
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    child=subprocess.Popen(a.command,env=env,start_new_session=True,preexec_fn=lambda:os.nice(10))
    def send(sig):
        if child.poll() is not None:return
        try:os.killpg(child.pid,sig)
        except ProcessLookupError:pass
        except PermissionError:
            # macOS can report EPERM for the already-exited process group.
            if child.poll() is None:raise
    quantum=.20;active=quantum*a.percent/100
    try:
        while child.poll() is None:
            send(signal.SIGCONT);time.sleep(active)
            send(signal.SIGSTOP);time.sleep(quantum-active)
    except BaseException:
        send(signal.SIGTERM);send(signal.SIGCONT)
        try:child.wait(timeout=5)
        except subprocess.TimeoutExpired:send(signal.SIGKILL)
        raise
    finally:send(signal.SIGCONT)
    raise SystemExit(child.wait())

if __name__=='__main__':main()
