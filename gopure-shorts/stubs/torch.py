# Lightweight stand-in: the AI Shorts path never touches torch.
class _Cuda:
    @staticmethod
    def is_available(): return False
cuda = _Cuda()
def device(*a, **k): return "cpu"
def set_num_threads(*a, **k): pass
def no_grad():
    import contextlib
    return contextlib.nullcontext()
__version__ = "0.0-stub"
