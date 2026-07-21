import os

# faiss-cpu and torch each bundle their own OpenMP runtime; loading both in one
# process on macOS aborts/segfaults unless this is set before either is imported.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
